import tempfile
import os
import os.path
import glob
import flask
import pathlib2
import subprocess
import time
import csv


ASSET_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'printer_assets')


class RealPrinter(object):
  def __init__(self):
    # Import here so that we don't require pycups unless we're trying to use a real printer
    import cups
    self._connection = cups.Connection()

  def print_picture(self, path):
    directory = tempfile.mkdtemp(prefix='tmp-artcade-')
    scaled_file = os.path.join(directory, 'scaled.jpg')
    # This resolution is slightly taller than 6:4 because the printer crops just a little too much of the picture when
    # printing full bleed. This forces it to crop mostly whitespace on the sides of the image. The top and bottom still
    # get cropped, but nothing we can do about that.
    subprocess.check_call(['convert', path, '-resize', '2048x1400^', '-gravity', 'center', '-extent', '2048x1400', scaled_file])

    printer_name = self._connection.getPrinters().keys()[0]
    self._connection.printFile(printer_name, scaled_file, 'print', {
      'MediaType': 'GlossyPaper',
      'StpiShrinkOutput': 'Expand',
      'PageSize': 'w288h432', # these are in points, 72 to an inch - so 4x6
      'StpFullBleed': 'True',
      'StpBorderless': 'True'
    })


class FakePrinter(object):
  def print_picture(self, path):
    print "pretending to print %s" % path
    # simulate some real delay
    time.sleep(1)


class ImageScanner(object):
  def __init__(self, directory, glob_pattern):
    self._directory = pathlib2.Path(directory)
    self._glob_pattern = glob_pattern

  @property
  def directory(self):
    return str(self._directory)

  def scan(self, count):
    # TODO: Do something smarter than loading paths to every single picture ever all at once. Also use pathlib
    # everywhere instead of just some places
    return [str(f.relative_to(self._directory)) for f in reversed(sorted(self._directory.glob(self._glob_pattern))[-count:])]


class EmailReporter(object):
  def __init__(self, csv_path):
    self._csv_path = csv_path

  def report_email(self, email_address):
    self._append_row(email_address, 'email')

  def report_image(self, email_address, image_path, printed):
    self._append_row(email_address, 'image', image_path, 'yes' if printed else 'no')

  def _append_row(self, email_address, row_type, image_path='', printed=''):
    with open(self._csv_path, 'a') as f:
      w = csv.writer(f)
      w.writerow([time.ctime(), email_address, row_type, image_path, printed])


class WebInterface(object):
  def __init__(self, image_scanner, printer, email_reporter):
    self._image_scanner = image_scanner
    self._printer = printer
    self._email_reporter = email_reporter

    app = flask.Flask('printer')
    self.app = app

    app.route('/')(self._index)
    app.route('/status')(self._status)
    app.route('/images/<path:path>')(self._image)
    app.route('/print/<path:path>', methods=['POST'])(self._print)
    app.route('/email/<path:path>', methods=['POST'])(self._email)
    app.route('/response', methods=['POST'])(self._response)
    app.route('/assets/<path:path>')(self._asset)

  def _index(self):
    return flask.send_file(os.path.join(ASSET_DIR, 'index.html'))

  def _status(self):
    files = _image_scanner.scan(50)
    return flask.jsonify(images=files)

  def _image(self, path):
    return flask.send_from_directory(self._image_scanner.directory, path)

  def _print(self, path):
    self._email_reporter.report_image(flask.request.form['email'], path, True)
    actual_path = flask.safe_join(self._image_scanner.directory, path)
    self._printer.print_picture(actual_path)
    return flask.jsonify(status='ok')

  def _email(self, path):
    self._email_reporter.report_image(flask.request.form['email'], path, False)
    return flask.jsonify(status='ok')

  def _response(self):
    self._email_reporter.report_email(flask.request.form['email'])
    return 'ok'

  def _asset(self, path):
    return flask.send_from_directory(ASSET_DIR, path)


_image_scanner = ImageScanner(os.getenv('ARTCADE_IMAGE_DIR'), os.getenv('ARTCADE_IMAGE_GLOB'))

if 'ARTCADE_DRY_RUN' in os.environ:
  _printer = FakePrinter()
else:
  _printer = RealPrinter()

_email_reporter = EmailReporter(os.getenv('ARTCADE_EMAIL_FILE'))

app = WebInterface(_image_scanner, _printer, _email_reporter).app
