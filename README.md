### How it works
1. Check youtube playlist
2. Download last episode (if new available)
3. Remove old episodes (if `EPISODES_LIMIT` not equal `0`)
3. Generate rss with all downloaded episodes

### Out of scope
- cron with `docker-compose up -d`
- nginx with `./data/files` directory
