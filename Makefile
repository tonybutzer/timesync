cat:
	cat Makefile



publish:
	git add .
	git commit -m 'auto commit from tony makefile nov2023'
	git push


git: publish


big:
	du -a . | sort -n -r | head -n 10
	echo HI
	find . -size +10M


nuke:
	rclone -P delete lc:dev-nlcd-developer/timesync
