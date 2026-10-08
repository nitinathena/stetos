/*
  CorAscult - Heart Sound Capture & Supabase Upload
  ESP32-S3 + INMP441 I2S MEMS Microphone

  Records N seconds of audio, builds a WAV file in PSRAM, and uploads it
  directly to Supabase Storage over HTTPS. No SD card needed.

  BEFORE UPLOADING, DO THIS:
  1. Fill in WIFI_SSID, WIFI_PASSWORD below
  2. Fill in SUPABASE_URL and SUPABASE_ANON_KEY (see setup guide in chat)
  3. Create a Storage bucket named "heart-sounds" in your Supabase project
     (public for quick prototyping, or private + an insert policy for anon)
  4. Adjust I2S_WS_PIN / I2S_SCK_PIN / I2S_SD_PIN to match your wiring

  Buffer is allocated from regular internal RAM (not PSRAM) since a
  5-second recording at 8kHz/16-bit is only ~80KB. If you later increase
  RECORD_SECONDS or SAMPLE_RATE well beyond this, you may need PSRAM
  instead - watch the "Free heap" print in Serial Monitor at startup.

  Library requirements: none beyond the standard ESP32 Arduino core
  (WiFi, HTTPClient, WiFiClientSecure, driver/i2s.h are all built in).
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "driver/i2s.h"

// ---------- USER CONFIG ----------
const char* WIFI_SSID     = "betterthanyesterday";
const char* WIFI_PASSWORD = "credosofabillion";

const char* SUPABASE_URL       = "https://hmvxfwgzwsimafwiwiet.supabase.co";
const char* SUPABASE_ANON_KEY  = "sb_publishable_qpeU-P0rBFDfyJ3QA9SyPA_4vLRJbtb";
const char* SUPABASE_BUCKET    = "heart-sounds";

// I2S pin mapping - adjust to match your wiring
#define I2S_WS_PIN   15   // LRCL / WS  (word select)
#define I2S_SCK_PIN  2    // BCLK / SCK (bit clock)
#define I2S_SD_PIN   13   // DOUT (mic data out -> ESP32 data in)

// Recording settings
#define SAMPLE_RATE      8000          // Hz - plenty for heart sounds (<1kHz content)
#define RECORD_SECONDS   5             // length of each recording
#define BITS_PER_SAMPLE  16
#define I2S_PORT         I2S_NUM_0

// ---------- DERIVED CONSTANTS ----------
#define NUM_SAMPLES     (SAMPLE_RATE * RECORD_SECONDS)
#define DATA_BYTES      (NUM_SAMPLES * (BITS_PER_SAMPLE / 8))
#define WAV_HEADER_SIZE 44

// Buffer lives in PSRAM (a 5s/8kHz/16-bit mono recording is ~80KB)
int16_t* audioBuffer = nullptr;

// ---------- WAV HEADER ----------
void writeWavHeader(uint8_t* header, uint32_t dataBytes) {
  uint32_t chunkSize    = 36 + dataBytes;
  uint32_t sampleRate   = SAMPLE_RATE;
  uint16_t numChannels  = 1;
  uint16_t bitsPerSample = BITS_PER_SAMPLE;
  uint32_t byteRate     = sampleRate * numChannels * bitsPerSample / 8;
  uint16_t blockAlign   = numChannels * bitsPerSample / 8;
  uint32_t subChunk1Size = 16;
  uint16_t audioFormat  = 1; // PCM

  memcpy(header,      "RIFF", 4);
  memcpy(header + 4,  &chunkSize, 4);
  memcpy(header + 8,  "WAVE", 4);
  memcpy(header + 12, "fmt ", 4);
  memcpy(header + 16, &subChunk1Size, 4);
  memcpy(header + 20, &audioFormat, 2);
  memcpy(header + 22, &numChannels, 2);
  memcpy(header + 24, &sampleRate, 4);
  memcpy(header + 28, &byteRate, 4);
  memcpy(header + 32, &blockAlign, 2);
  memcpy(header + 34, &bitsPerSample, 2);
  memcpy(header + 36, "data", 4);
  memcpy(header + 40, &dataBytes, 4);
}

// ---------- I2S SETUP ----------
void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT, // INMP441 sends 24-bit data in a 32-bit frame
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD_PIN
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
  i2s_zero_dma_buffer(I2S_PORT);
}

// ---------- RECORD AUDIO ----------
void recordAudio() {
  Serial.println("Recording...");
  size_t bytesRead = 0;
  int32_t rawSample;
  int sampleIndex = 0;

  while (sampleIndex < NUM_SAMPLES) {
    i2s_read(I2S_PORT, &rawSample, sizeof(int32_t), &bytesRead, portMAX_DELAY);
    if (bytesRead > 0) {
      // INMP441 gives 24-bit data left-justified in a 32-bit word -> shift down to 16-bit
      int16_t sample16 = (int16_t)(rawSample >> 14);
      audioBuffer[sampleIndex++] = sample16;
    }
  }
  Serial.println("Recording complete.");
}

// ---------- UPLOAD TO SUPABASE STORAGE ----------
bool uploadToSupabase(uint8_t* wavData, size_t wavSize, String filename) {
  WiFiClientSecure client;
  client.setInsecure(); // OK for prototyping; pin the root CA for a production build

  HTTPClient https;
  String url = String(SUPABASE_URL) + "/storage/v1/object/" + String(SUPABASE_BUCKET) + "/" + filename;

  https.begin(client, url);
  https.addHeader("Content-Type", "audio/wav");
  https.addHeader("apikey", SUPABASE_ANON_KEY);
  https.addHeader("Authorization", "Bearer " + String(SUPABASE_ANON_KEY));

  Serial.println("Uploading to Supabase...");
  int code = https.POST(wavData, wavSize);
  Serial.printf("Upload response code: %d\n", code);

  bool success = (code == 200);
  if (!success) {
    Serial.println(https.getString());
  } else {
    Serial.println("Upload successful!");
  }
  https.end();
  return success;
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Allocate recording buffer from the regular heap (internal SRAM).
  // At 8kHz/16-bit/5s this is ~80KB, which fits fine without PSRAM.
  Serial.printf("Free heap before allocation: %u bytes\n", ESP.getFreeHeap());
  audioBuffer = (int16_t*)malloc(DATA_BYTES);
  if (audioBuffer == nullptr) {
    Serial.println("Allocation failed! Try reducing RECORD_SECONDS or SAMPLE_RATE.");
    while (1) delay(1000);
  }

  setupI2S();

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected: " + WiFi.localIP().toString());
}

// ---------- MAIN LOOP ----------
void loop() {
  recordAudio();

  // Build WAV file: header + PCM data, contiguous in one buffer for upload
  uint8_t* wavFile = (uint8_t*)malloc(WAV_HEADER_SIZE + DATA_BYTES);
  writeWavHeader(wavFile, DATA_BYTES);
  memcpy(wavFile + WAV_HEADER_SIZE, audioBuffer, DATA_BYTES);

  String filename = "sample_" + String(millis()) + ".wav";
  uploadToSupabase(wavFile, WAV_HEADER_SIZE + DATA_BYTES, filename);

  free(wavFile);

  Serial.println("Waiting 10s before next recording... (swap this for a button trigger later)");
  delay(10000);
}
