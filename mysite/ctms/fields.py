import sys
from io import BytesIO

from django.core.exceptions import ValidationError
from django.utils import six
from django.forms.fields import ImageField


class SvgAllowedImageField(ImageField):
    """
    Custom ImageField which allows uploading svg images
    """

    def to_python(self, data):
        f = super(ImageField, self).to_python(data)
        if f is None:
            return None

        from PIL import Image

        if hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file = BytesIO(data.read())
            else:
                file = BytesIO(data['content'])

        try:
            # load() could spot a truncated JPEG, but it loads the entire
            # image in memory, which is a DoS vector. See #3848 and #18520.
            image = Image.open(file)
            # verify() must be called immediately after the constructor.
            image.verify()

            # Annotating so subclasses can reuse it for their own validation
            f.image = image
            # Pillow doesn't detect the MIME type of all formats. In those
            # cases, content_type will be None.
            f.content_type = Image.MIME.get(image.format)
        except Exception:
            if data.name.split('.')[-1] != 'svg':
                six.reraise(ValidationError, ValidationError(
                    self.error_messages['invalid_image'],
                    code='invalid_image',
                ), sys.exc_info()[2])
            f.image = file
            f.content_type = 'text/svg'
        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f
