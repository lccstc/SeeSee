module.exports = {
  apps: [
    {
      name: "bookkeeping-core",
      cwd: "/ABS/PATH/TO/SeeSee/wxbot/bookkeeping-platform",
      script: "/ABS/PATH/TO/SeeSee/wxbot/bookkeeping-platform/.venv/bin/gunicorn",
      interpreter: "none",
      args: "--workers 2 --threads 8 --worker-class gthread --bind 0.0.0.0:8765 --timeout 120 --graceful-timeout 30 --keep-alive 5 --access-logfile - --error-logfile - wsgi:app",
      env: {
        PYTHONPATH: "/ABS/PATH/TO/SeeSee/wxbot/bookkeeping-platform",
        BOOKKEEPING_CORE_TOKEN: "REPLACE_WITH_CORE_TOKEN",
        BOOKKEEPING_DB_DSN: "postgresql://USER:PASSWORD@127.0.0.1:5432/bookkeeping",
        BOOKKEEPING_MASTER_USERS: "user1,user2",
        BOOKKEEPING_AUTO_BACKUP_ON_CLOSE: "1",
        BOOKKEEPING_BACKUP_DIR: "/ABS/PATH/TO/SeeSee/backups/postgres",
        BOOKKEEPING_BACKUP_KEEP_DAYS: "14",
      },
      autorestart: true,
      max_restarts: 30,
      min_uptime: "10s",
      restart_delay: 3000,
    },
  ],
};
