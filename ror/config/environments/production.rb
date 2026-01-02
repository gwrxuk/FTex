# frozen_string_literal: true

require 'active_support/core_ext/integer/time'

Rails.application.configure do
  # Code is not reloaded between requests.
  config.enable_reloading = false

  # Eager load code on boot.
  config.eager_load = true

  # Full error reports are disabled
  config.consider_all_requests_local = false

  # Caching
  config.action_controller.perform_caching = true

  # Store files on local file system
  config.active_storage.service = :local if defined?(ActiveStorage)

  # Force all access to the app over SSL
  config.force_ssl = ENV['FORCE_SSL'].present?

  # Log to STDOUT
  config.logger = ActiveSupport::Logger.new($stdout)
    .tap  { |logger| logger.formatter = ::Logger::Formatter.new }
    .then { |logger| ActiveSupport::TaggedLogging.new(logger) }

  # Prepend all log lines with the following tags.
  config.log_tags = [:request_id]

  # Log level
  config.log_level = ENV.fetch('RAILS_LOG_LEVEL', 'info').to_sym

  # Use default logging formatter
  config.active_support.report_deprecations = false

  # Do not dump schema after migrations.
  config.active_record.dump_schema_after_migration = false

  # Enable DNS rebinding protection
  config.hosts = ENV.fetch('ALLOWED_HOSTS', '').split(',').map(&:strip)
  config.hosts << 'localhost'
  config.hosts << /.*\.ftex\.local/
end

