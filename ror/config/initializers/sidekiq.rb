# frozen_string_literal: true

require 'sidekiq'
require 'sidekiq-scheduler'

# Redis connection configuration
redis_url = ENV.fetch('REDIS_URL', 'redis://redis:6379/1')

Sidekiq.configure_server do |config|
  config.redis = { url: redis_url, network_timeout: 5 }

  # Enable Sidekiq Scheduler
  config.on(:startup) do
    Sidekiq.schedule = YAML.load_file(Rails.root.join('config/sidekiq.yml'))[:schedule] || {}
    Sidekiq::Scheduler.reload_schedule!
  end

  # Error handling
  config.error_handlers << proc { |ex, context|
    Rails.logger.error("Sidekiq error: #{ex.message}")
    Rails.logger.error("Context: #{context}")
    Rails.logger.error(ex.backtrace.join("\n")) if ex.backtrace
  }

  # Death handler - when a job exhausts all retries
  config.death_handlers << proc { |job, ex|
    Rails.logger.error("Job #{job['class']} died: #{ex.message}")
    # Could notify monitoring system here
  }
end

Sidekiq.configure_client do |config|
  config.redis = { url: redis_url, network_timeout: 5 }
end

# Configure default job options
Sidekiq.default_job_options = {
  'backtrace' => true,
  'retry' => 5
}

