# gunicorn -b '' --reload -p gu.pid -D --access-logfile log.log --error-logfile err.log  -n celcat-ext -R

bind='0.0.0.0:32769'

workers=2

pidfile='gu.pid'
daemon=True

accesslog='gunicorn_access.log'
errorlog='gunicorn_error.log'
capture_output=True
loglevel='debug'

reload=True

enable_stdio_inheritance=True

proc_name='celcat_ext'
