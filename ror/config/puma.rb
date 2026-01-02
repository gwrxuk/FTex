# frozen_string_literal: true

# Puma configuration for the FTex Worker API

# Threads
max_threads_count = ENV.fetch('RAILS_MAX_THREADS', 5)
min_threads_count = ENV.fetch('RAILS_MIN_THREADS') { max_threads_count }
threads min_threads_count, max_threads_count

# Workers
worker_count = ENV.fetch('WEB_CONCURRENCY', 2)
workers worker_count

# Port
port ENV.fetch('PORT', 3001)

# Environment
environment ENV.fetch('RAILS_ENV', 'development')

# Preload app for memory savings
preload_app!

# Allow puma to be restarted by `bin/rails restart` command.
plugin :tmp_restart

on_worker_boot do
  ActiveRecord::Base.establish_connection if defined?(ActiveRecord)
end

