cat:
	cat Makefile


down:
	(cd /tmp; curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip)
	(cd /tmp; unzip rclone-current-linux-amd64.zip)


install:
	(cd /tmp/rclone-*-linux-amd64; sudo cp rclone /usr/bin/)
	sudo chown root:root /usr/bin/rclone
	sudo chmod 755 /usr/bin/rclone
