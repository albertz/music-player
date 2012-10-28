#!/usr/bin/env ruby

# https://github.com/wereHamster/ghup
# https://gist.github.com/2668995
#   gem install json
#   git config --global github.user YOUR_USER
#   git config --global github.token YOUR_TOKEN
# For the token, see:
# https://help.github.com/articles/creating-an-oauth-token-for-command-line-use

require 'rubygems'

require 'json'
require 'net/https'
require 'pathname'



# Extensions
# ----------

# We extend Pathname a bit to get the content type.
class Pathname
  def type
    flags = RUBY_PLATFORM =~ /darwin/ ? 'Ib' : 'ib'
    `file -#{flags} #{realpath}`.chomp.gsub(/;.*/,'')
  end
end

def die(message, with_usage = false)
	puts "ERROR: #{message}"
	puts %Q|Usage: #{__FILE__} file_to_upload [repo]
	file_to_upload: File to be uploaded.
	repo: GitHub repo to upload to.  Ex: "tekkub/sandbox".  If omitted, the repo from `git remote show origin` will be used.| if with_usage
	exit 1
end


# Helpers
# -------

# Do a post to the given url, with the payload and optional basic auth.
def post(url, token, params, headers)
  puts "post to #{url}"
  uri = URI.parse(url)

  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true

  req = Net::HTTP::Post.new(uri.path, headers)
  req['Authorization'] = "token #{token}" if token

  return http.request(req, params)
end

def get(url, token, headers)
	uri = URI.parse(url)
	
	http = Net::HTTP.new(uri.host, uri.port)
	http.use_ssl = true
	
	req = Net::HTTP::Get.new(uri.path, headers)
	req['Authorization'] = "token #{token}" if token
	
	return http.request(req)
end

def delete(url, token, headers)
	uri = URI.parse(url)
	
	http = Net::HTTP.new(uri.host, uri.port)
	http.use_ssl = true
	
	req = Net::HTTP::Delete.new(uri.path, headers)
	req['Authorization'] = "token #{token}" if token
	
	return http.request(req)
end

def urlencode(str)
  str.gsub(/[^a-zA-Z0-9_\.\-]/n) {|s| sprintf('%%%02x', s[0].to_i) }
end

# Yep, ruby net/http doesn't support multipart. Write our own multipart generator.
# The order of the params is important, the file needs to go as last!
def build_multipart_content(params)
	parts, boundary = [], "#{rand(1000000)}-we-are-all-doomed-#{rand(1000000)}"
	
	params.each do |name, value|
		data = []
		if value.is_a?(Pathname) then
			data << "Content-Disposition: form-data; name=\"#{urlencode(name.to_s)}\"; filename=\"#{value.basename}\""
			data << "Content-Type: #{value.type}"
			data << "Content-Length: #{value.size}"
			data << "Content-Transfer-Encoding: binary"
			data << ""
			data << IO.read(value.cleanpath)
			else
			data << "Content-Disposition: form-data; name=\"#{urlencode(name.to_s)}\""
			data << ""
			data << value
		end
		
		parts << data.join("\r\n") + "\r\n"
	end
	
	[ "--#{boundary}\r\n" + parts.join("--#{boundary}\r\n") + "--#{boundary}--", {
		"Content-Type" => "multipart/form-data; boundary=#{boundary}"
	}]
end



# Configuration and setup
# -----------------------

# Get Oauth token for this script.
token = `git config --get github.token`.chomp

# The file we want to upload, and repo where to upload it to.
file = Pathname.new(ARGV[0])
repo = ARGV[1] || `git config --get remote.origin.url`.match(/git@github.com:(.+?)\.git/)[1]



# The actual, hard work
# ---------------------

# List
res = get("https://api.github.com/repos/#{repo}/downloads", token, {})
info = JSON.parse(res.body)
info.each do |fileinfo|
	if fileinfo["name"] == file.basename.to_s
		puts "File already exists, deleting..."
		res = delete("https://api.github.com/repos/#{repo}/downloads/#{fileinfo['id']}", token, {})
		break
	end
end

# Register the download at github.
puts "Registering download..."
res = post("https://api.github.com/repos/#{repo}/downloads", token, {
  'name' => file.basename.to_s, 'size' => file.size.to_s,
  'content_type' => file.type.gsub(/;.*/, '')
}.to_json, {})

info = JSON.parse(res.body)
die("Error") if res.class == Net::HTTPClientError
die("GitHub doens't want us to upload the file.") unless res.class == Net::HTTPCreated

# Parse the body and use the info to upload the file to S3.
#res = post(info['s3_url'], nil, *build_multipart_content({
#  'key' => info['path'], 'acl' => info['acl'], 'success_action_status' => 201,
#  'Filename' => info['name'], 'AWSAccessKeyId' => info['accesskeyid'],
#  'Policy' => info['policy'], 'Signature' => info['Signature'],
#  'Content-Type' => info['mime_type'], 'file' => file
#}))
#
#die("S3 is mean to us.") unless res.class == Net::HTTPCreated

system(
	"curl " +
	"-F 'key=#{info['path']}' " +
	"-F 'acl=#{info['acl']}' " +
	"-F 'success_action_status=201' " +
	"-F 'Filename=#{info['name']}' " +
	"-F 'AWSAccessKeyId=#{info['accesskeyid']}' " +
	"-F 'Policy=#{info['policy']}' " +
	"-F 'Signature=#{info['signature']}' " +
	"-F 'Content-Type=#{info['mime_type']}' " +
	"-F 'file=@#{file.cleanpath}' " +
	"#{info['s3_url']}"
)

# Print the URL to the file to stdout.
puts "#{info['s3_url']}#{info['path']}"
