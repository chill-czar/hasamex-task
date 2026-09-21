const path = require("path");

const ROOT_DIR = __dirname;

module.exports = {
  apps: [
    {
      name: "hasamex-api",
      script: path.join(ROOT_DIR, ".venv/bin/uvicorn"),
      args: "apps.api.app.main:app --host 127.0.0.1 --port 8000",
      cwd: ROOT_DIR,
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 2000,
      max_memory_restart: "400M",
      env: {
        PORT: "8000",
      },
    },
    {
      name: "hasamex-web",
      script: "npm",
      args: "run start -- -p 3000 -H 127.0.0.1",
      cwd: path.join(ROOT_DIR, "apps/web"),
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 2000,
      max_memory_restart: "600M",
      env: {
        NODE_ENV: "production",
        PORT: "3000",
      },
    },
  ],
};
