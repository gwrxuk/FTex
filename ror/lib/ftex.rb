# frozen_string_literal: true

# FTex module namespace
module Ftex
  class << self
    def config
      @config ||= Configuration.new
    end

    def configure
      yield config
    end

    def logger
      @logger ||= Rails.logger
    end
  end

  class Configuration
    attr_accessor :api_url, :api_timeout, :retry_count

    def initialize
      @api_url = ENV.fetch('FTEX_API_URL', 'http://backend:8000')
      @api_timeout = ENV.fetch('FTEX_API_TIMEOUT', 30).to_i
      @retry_count = ENV.fetch('FTEX_RETRY_COUNT', 3).to_i
    end
  end
end

