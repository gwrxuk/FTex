# frozen_string_literal: true

require_relative 'boot'

require 'rails'
require 'active_model/railtie'
require 'active_job/railtie'
require 'active_record/railtie'
require 'action_controller/railtie'

# Load dotenv in development/test
Bundler.require(*Rails.groups)
Dotenv::Rails.load if defined?(Dotenv)

module FtexWorker
  class Application < Rails::Application
    config.load_defaults 7.1

    # API-only mode
    config.api_only = true

    # Time zone
    config.time_zone = 'UTC'

    # ActiveJob adapter
    config.active_job.queue_adapter = :sidekiq

    # Autoload lib directory
    config.autoload_lib(ignore: %w[assets tasks])

    # Eager load paths
    config.eager_load_paths << Rails.root.join('app/workers')
    config.eager_load_paths << Rails.root.join('app/services')
    config.eager_load_paths << Rails.root.join('lib')
  end
end

