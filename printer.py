import cups
import tempfile
import os
import os.path
import glob
import flask
import pathlib2


class Printer(object):
  def __init__(self):
    self._connection = cups.Connection()

  def print_picture(self, path):
    directory = tempfile.mkdtemp(prefix='tmp-artcade-')
    scaled_file = os.path.join(directory, 'scaled.jpg')
    # This resolution is slightly taller than 6:4 because the printer crops just a little too much of the picture when
    # printing full bleed. This forces it to crop mostly whitespace on the sides of the image. The top and bottom still
    # get cropped, but nothing we can do about that.
    subprocess.check_call['convert', path, '-resize', '2048x1400^', '-gravity', 'center', '-extent', '2048x1400', scaled_file]

    printer_name = self._connection.getPrinters().keys()[0]
    self._connection.printFile(printer_name, scaled_file, 'print', {
      'MediaType': 'GlossyPaper',
      'StpiShrinkOutput': 'Expand',
      'PageSize': 'w288h432', # these are in points, 72 to an inch - so 4x6
      'StpFullBleed': 'True',
      'StpBorderless': 'True'
    })


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
    return [str(f.relative_to(self._directory)) for f in sorted(self._directory.glob(self._glob_pattern))[-count:]]


class WebInterface(object):
  def __init__(self, image_scanner, printer):
    self._image_scanner = image_scanner
    self._printer = printer

    app = flask.Flask('printer')
    self.app = app

    app.route('/')(self._index)
    app.route('/status')(self._status)
    app.route('/images/<path:path>')(self._image)
    app.route('/print/<path:path>', methods=['POST'])(self._print)

  def _index(self):
    pass

  def _status(self):
    files = _image_scanner.scan(50)
    return flask.jsonify(images=files)

  def _image(self, path):
    flask.send_from_directory(self._image_scanner.directory, path)

  def _print(self, path):
    actual_path = flask.safe_join(self._image_scanner.directory, path)
    self._printer.print_picture(actual_path)
    return flask.jsonify(status='ok')


_image_scanner = ImageScanner(os.getenv('ARTCADE_IMAGE_DIR'), os.getenv('ARTCADE_IMAGE_GLOB'))
_printer = Printer()
app = WebInterface(_image_scanner, _printer).app
