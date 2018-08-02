aapt list -a $1 | sed -n '/ activity /{:loop n;s/^.*android:name.*="\([^"]\{1,\}\)".*/\1/;T loop;p;t}'
