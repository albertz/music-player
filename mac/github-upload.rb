require 'tempfile'
require 'nokogiri'
require 'httpclient'
require 'stringio'
require 'json'
require 'faster_xml_simple'

module Net
  module GitHub
    class Upload
      VERSION = '0.0.8'
      def initialize params=nil
        @login = params[:login]
        @token = params[:token]

        if @login.empty? or @token.empty?
          raise "login or token is empty"
        end
      end

      # Upload a file to github. Will fail if the file already exists.
      # To upload, either supply :data and :name or :file.
      #
      # @param [Hash] info
      # @option info [String] :content_type ('application/octet-stream') Type of data to send 
      # @option info [String] :data Data to upload as a file. Requires that the :name option is set.
      # @option info [String] :description ('') Description of file on Github download page.
      # @option info [String] :file Path to file to upload.
      # @option info [String] :name (filename of info[:file] if uploading a file) Name the file will have (not including path) when uploaded.
      # @option info [Boolean] :replace (false) True to force overwriting of an existing file.
      # @option info [String] :repos Name of Github project, such as "my_project", which is the repository.
      # @option info [Float] :upload_timeout (120) Maximum time, in seconds, before abandoning a file upload.
      # @option info [Float] :yield_interval (1) Interval, in seconds, between yields if block is given.     
      # @yield [] Optional block will yield every info[:yield_interval] seconds (This can be used, for example, to print "#" every second so users see that the upload is continuing).
      def upload info
        unless info[:repos]
          raise "required repository name"
        end
        info[:repos] = @login + '/' + info[:repos] unless info[:repos].include? '/'

        if info[:file]
          file = info[:file]
          unless File.exist?(file) && File.readable?(file)
            raise "file does not exsits or readable"
          end
          info[:name] ||= File.basename(file)
        end
        unless  info[:file] || info[:data]
          raise "required file or data parameter to upload"
        end

        unless info[:name]
          raise "required name parameter for filename with data parameter"
        end

        if info[:replace]
          list_files(info[:repos]).each { |obj|
            next unless obj[:name] == info[:name]
            delete info[:repos], obj[:id]
          }
        elsif list_files(info[:repos]).any?{|obj| obj[:name] == info[:name]}
          raise "file '#{info[:name]}' is already uploaded. please try different name"
        end

        info[:content_type] ||= 'application/octet-stream'
        stat = HTTPClient.post("https://github.com/#{info[:repos]}/downloads", {
          "file_size"    => info[:file] ? File.stat(info[:file]).size : info[:data].size,
          "content_type" => info[:content_type],
          "file_name"    => info[:name],
          "description"  => info[:description] || '',
          "login"        => @login,
          "token"        => @token
        })

        unless stat.code == 200
          raise "Failed to post file info"
        end

        upload_info = JSON.parse(stat.content)
        if info[:file]
          f = File.open(info[:file], 'rb')
        else
          f = Tempfile.open('net-github-upload')
          f << info[:data]
          f.flush
        end
        client = HTTPClient.new
        client.send_timeout = info[:upload_timeout] if info[:upload_timeout]

        res = begin
          connection = client.post_async("http://github.s3.amazonaws.com/", [
              ['Filename', info[:name]],
              ['policy', upload_info['policy']],
              ['success_action_status', 201],
              ['key', upload_info['path']],
              ['AWSAccessKeyId', upload_info['accesskeyid']],
              ['Content-Type', upload_info['content_type'] || 'application/octet-stream'],
              ['signature', upload_info['signature']],
              ['acl', upload_info['acl']],
              ['file', f]
          ])

          until connection.finished?
            yield if block_given?
            sleep info[:yield_interval] || 1
          end

          connection.pop
        ensure
          f.close
        end

        if res.status == 201
          return FasterXmlSimple.xml_in(res.body.read)['PostResponse']['Location']
        else
          raise 'Failed to upload' + extract_error_message(res.body)
        end
      end

      # Upload a file and replace it if it already exists on the server.
      #
      # @see #upload
      def replace info = {}, &block
         upload info.merge( :replace => true ), &block
      end

      # Delete all uploaded files.
      def delete_all repos
        unless repos
          raise "required repository name"
        end
        repos = @login + '/' + repos unless repos.include? '/'
        list_files(repos).each { |obj|
          delete repos, obj[:id]
        }
      end

      # Delete an individual file (used by #replace when replacing existing files).
      def delete repos, id
        HTTPClient.post("https://github.com/#{repos}/downloads/#{id.gsub( "download_", '')}", {
          "_method"      => "delete",
          "login"        => @login,
          "token"        => @token
        })
      end

      # List all the files uploaded to a repository.
      def list_files repos
        raise "required repository name" unless repos
        res = HTTPClient.get_content("https://github.com/#{repos}/downloads", {
          "login" => @login,
          "token" => @token
        })
        Nokogiri::HTML(res).xpath('id("manual_downloads")/li').map do |fileinfo|
          obj = {
            :description =>  fileinfo.at_xpath('descendant::h4').text.force_encoding('BINARY').gsub(/.+?\xe2\x80\x94 (.+?)(\n\s*)?$/m, '\1'),
            :date => fileinfo.at_xpath('descendant::p/time').attribute('title').text,
            :size => fileinfo.at_xpath('descendant::p/strong').text,
            :id => /\d+$/.match(fileinfo.at_xpath('a').attribute('href').text)[0]
          }
          anchor = fileinfo.at_xpath('descendant::h4/a')
          obj[:link] = anchor.attribute('href').text
          obj[:name] = anchor.text
          obj
        end
      end

      private

      def extract_error_message(stat)
        # @see http://docs.amazonwebservices.com/AmazonS3/2006-03-01/ErrorResponses.html
        error = FasterXmlSimple.xml_in(stat.content)['Error']
        " due to #{error['Code']} (#{error['Message']})"
      rescue
        ''
      end
    end
  end
end
