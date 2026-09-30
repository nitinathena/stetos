import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false, // don't auto-generate AGENTS.md/CLAUDE.md on every dev/build
};

export default nextConfig;
