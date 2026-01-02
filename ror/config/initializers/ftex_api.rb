# frozen_string_literal: true

# FTex Backend API Client Configuration
module Ftex
  class ApiClient
    include Singleton

    attr_reader :connection

    def initialize
      @base_url = ENV.fetch('FTEX_API_URL', 'http://backend:8000')
      @connection = build_connection
    end

    def get(path, params = {})
      response = connection.get(path, params)
      parse_response(response)
    end

    def post(path, body = {})
      response = connection.post(path) do |req|
        req.headers['Content-Type'] = 'application/json'
        req.body = Oj.dump(body, mode: :compat)
      end
      parse_response(response)
    end

    private

    def build_connection
      Faraday.new(url: @base_url) do |f|
        f.request :retry, {
          max: 3,
          interval: 0.5,
          backoff_factor: 2,
          exceptions: [Faraday::ConnectionFailed, Faraday::TimeoutError]
        }
        f.response :raise_error
        f.adapter Faraday.default_adapter
      end
    end

    def parse_response(response)
      Oj.load(response.body, symbol_keys: true)
    rescue Oj::ParseError
      response.body
    end
  end
end

