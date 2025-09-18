PROCFILE = """
web: exec bundle exec unicorn -c config/unicorn.rb -p $PORT
crons: exec supercronic -passthrough-logs crontabs/crontab
sidekiq: exec bundle exec sidekiq -q default
"""

APTIBLE_YAML = """
before_deploy:
  - if [ -n "$DB_CREATE" ]; then bundle exec rake db:create; fi
  - if [ -n "$RUN_MIGRATIONS" ]; then bundle exec rake db:migrate; fi
after_deploy_success:
  - ./alert_slack_success.sh
after_deploy_failure:
  - ./alert_slack_failure.sh
"""
