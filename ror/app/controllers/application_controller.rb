# frozen_string_literal: true

class ApplicationController < ActionController::API
  rescue_from StandardError, with: :handle_error

  private

  def handle_error(exception)
    Rails.logger.error("Unhandled error: #{exception.message}")
    Rails.logger.error(exception.backtrace.first(10).join("\n"))

    render json: {
      error: exception.message,
      status: 'error'
    }, status: :internal_server_error
  end
end

