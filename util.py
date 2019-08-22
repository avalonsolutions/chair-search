import io
import base64
import numpy as np
import cv2
from skimage.morphology import skeletonize
import skimage

import googleapiclient.discovery
from PIL import Image


def predict_json(project, model, input, version=None):
    """Send json data to a deployed model for prediction.
​
    Args:
        project (str): project where the Cloud ML Engine Model is deployed.
        model (str): model name.
        input dict(dict()): Dictionary in the form of {'image_bytes': {"b64": input_string}}
        version: str, version of the model to target.
    Returns:
        Mapping[str: any]: dictionary of prediction results defined by the
            model.
    """
    # Create the ML Engine service object.
    service = googleapiclient.discovery.build('ml', 'v1')
    name = 'projects/{}/models/{}'.format(project, model)

    if version is not None:
        name += '/versions/{}'.format(version)

    response = service.projects().predict(name=name, body={'instances': input}).execute()
    if 'error' in response:
        raise RuntimeError(response['error'])

    return response['predictions'][0]['output_bytes']['b64']  # TODO: Make this just return json, not list


def crop_image(img):
    """Crops input image to 256x256. Not used anymore."""

    basewidth = 256
    img = Image.open(io.BytesIO(base64.b64decode(img.split(',')[1])))
    # img = Image.open('somepic.jpg')
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    # img.save('sompic.jpg')
    from io import BytesIO

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def sketch(src):
    """
    from https://github.com/whigy/pix2pix-tensorflow/blob/master/tools/process.py
    Not used
    """
    # Process sketch to fit input. Only used for test input
    src = np.asarray(src * 255, np.uint8)
    # Crop the sketch and minimize white padding.
    cropped = crop_and_resize(src, return_gray=True)
    # Skeletonize the lines
    skeleton = skeletonize(cropped / 255)
    final = 1 - np.float32(skeleton)
    return np.asarray(src, np.float32)


def crop_and_resize(src, return_gray=False):
    """
    from https://github.com/whigy/pix2pix-tensorflow/blob/master/tools/process.py
    crop edge image to discard white pad, and resize to training size
    based on: https://stackoverflow.com/questions/48395434/how-to-crop-or-remove-white-background-from-an-image
    [OBS!] only works on image with white background
    """

    src = np.array(Image.open(io.BytesIO(base64.b64decode(src.split(',')[1]))))
    # src = np.array(pillow_image)
    # processed = crop_and_resize(src)
    # test = encode(processed)

    height, width, _ = src.shape

    # (1) Convert to gray, and threshold
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    th, threshed = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # (2) Morph-op to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

    # (3) Find the max-area contour
    cnts = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    cnt = sorted(cnts, key=cv2.contourArea)[-1]

    # (4) Crop
    x, y, w, h = cv2.boundingRect(cnt)
    x_1 = max(x, x - 10)
    y_1 = max(y, y - 10)
    x_2 = min(x + w, width)
    y_2 = min(y + h, height)
    if return_gray:
        dst = gray[y_1:y_2, x_1:x_2]
    else:
        dst = src[y_1:y_2, x_1:x_2]
    # pad white to resize
    height = int(max(0, w - h) / 2.0)
    width = int(max(0, h - w) / 2.0)
    padded = cv2.copyMakeBorder(dst, height, height, width, width, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    return encode(np.asarray(cv2.resize(padded, (256, 256), interpolation=cv2.INTER_AREA)))


def encode(image) -> str:
    # convert image to bytes
    with io.BytesIO() as output_bytes:
        PIL_image = Image.fromarray(skimage.img_as_ubyte(image))
        PIL_image.save(output_bytes, 'PNG')  # Note JPG is not a vaild type here
        bytes_data = output_bytes.getvalue()

    # encode bytes to base64 string
    base64_str = str(base64.b64encode(bytes_data), 'utf-8')
    return base64_str


if __name__ == '__main__':
    img = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAQH0lEQVR4Xu2dWchXVfuGnzdT621QM80hG0wbITIsJBo0qAgMtKgoCiGKPKiTDhooyIOi4aCD6kQaIIIiAhGyg4qyGSHCiLLBqTKHNDPTMjN7P+7Ff/snPvmc1tru9d7XhhcadO39XPfj5Vrrt3979/T19fUFBwQgYEmgBwFY5k7REEgEEACNAAFjAgjAOHxKhwACoAcgYEwAARiHT+kQQAD0AASMCSAA4/ApHQIIgB6AgDEBBGAcPqVDAAHQAxAwJoAAjMOndAggAHoAAsYEEIBx+JQOAQRAD0DAmAACMA6f0iGAAOgBCBgTQADG4VM6BBAAPQABYwIIwDh8SocAAqAHIGBMAAEYh0/pEEAA9AAEjAkgAOPwKR0CCIAegIAxAQRgHD6lQwAB0AMQMCaAAIzDp3QIIAB6AALGBBCAcfiUDgEEQA9AwJgAAjAOn9IhgADoAQgYE0AAxuFTOgQQAD0AAWMCCMA4fEqHAAKgByBgTAABGIdP6RBAAPQABIwJIADj8CkdAgiAHoCAMQEEYBw+pUMAAdADEDAmgACMw6d0CCAAegACxgQQgHH4lA4BBEAPQMCYAAIwDp/SIYAA6AEIGBNAAMbhUzoEEAA9AAFjAgjAOHxKhwACoAcgYEwAARiHT+kQQAD0AASMCSAA4/ApHQIIgB6AgDEBBGAcPqVDAAHQAxAwJoAAjMOndAggAHoAAsYEEIBx+JQOAQRAD0DAmAACMA6f0iGAAOgBCBgTQADG4VM6BBAAPQABYwIIwDh8SocAAqAHIGBMAAEYh0/pEEAA9AAEjAkgAOPwKR0CCIAegIAxAQRgHD6lQwAB0AMQMCaAAIzDp3QIIAB6AALGBBCAcfiUDgEEQA9AwJgAAjAOn9IhgADoAQgYE0AAxuFTOgQQAD0AAWMCCMA4fEqHAAKgByBgTAABGIdP6RBAAPQABIwJIADj8CkdAgiAHoCAMQEEYBw+pUMAAdADEDAmgACMw6d0CCAAegACxgQQgHH4lA4BBEAPQMCYAAIwDp/SIYAA6AEIGBNAAMbhUzoEEAA9AAFjAgjAOHxKhwACoAcgYEwAARiHT+kQQAD0AASMCSAA4/ApHQIIgB6AgDEBBGAcPqVDAAHQAxAwJoAAjMOndAggAHoAAsYEEIBx+JQOAQRAD0DAmAACMA6f0iGAAOgBCBgTQADG4VM6BBAAPQABYwIIwDh8SodAKwKYNm1aDBo0KI4++ugYMmRIDBs2LI455pgYPnx4HHvssTFy5Mg47rjjYtSoUXHUUUeRCgQg0BKBVgRw0UUXxT///BNbt26NP/74I7Zt2xZ//vln/PXXX7Fjx474+++/Y+fOndHX15fK7unpiQEDBsShhx4aAwcOTPI47LDD4vDDD4/e3t448sgjkyhOPvnk9HPqqafGWWedFRMnTmwJG6eBQP8g0IoA9gXVli1bYt26dfHTTz/F+vXr4+eff46NGzfGL7/8Eps2bYrNmzfHhg0b4vfff0//T/8uqUgmEoikIVlIEppljBgxIsaMGRMnnnhiTJgwIU477bQ4++yz02yEAwLuBDongAMJ5LfffovPP/88vv7661i+fHl8//33sWbNmiQSyUNy2b59e5pxaJahmYVmFFqWaCkiaWg5MnTo0CQP/TcJRP9t9OjR6Uf/zAGB/kKgXwlgX0JZunRpLFmyJL755ptYuXJlfPfdd2k2IUloRqEfyaIRhqShZczuliiDBw/etTw54ogj0vJEUpFItN+hvY5GJI1Mxo4dm2YqHBA4mARsBbC/0LV3sXr16li7dm2aWehHSxItUzTL+PXXX3eJRMuUZs9DItndfschhxySli36kUj0o1mJRNLsdYwbNy5OOOGEOOmkk9Iy5vTTT08zFA4IHCgBBHCgBA/g90seEkkjE4lE+xra75BI9P8lEf27ljf6Z4lEG6ZawjT7HZKFZhyaaWiGodmFhKENUm2MShjMNg4gqH78WxFApeFqFtLsdWj58uOPP6bNU0mk2e9oNke1dGn2PCQCLVG0PJEw9NGrhKFN0vHjx6dPVPTD4UEAAXjkHN9++236WbFiRdoclUAkjOaTFO19NB/N6tMULU2aTVIJQ3sZ2seQMI4//vi0HDnllFPS7EIC4aiTAAKoM7eiVy0RaHahjVIJY9WqVUkYWpJor0ObpVqO6Ndpc1TC0H0b2r/QckQfsWqPQssSiaLZv2iWI5p9cHSDAALoRg5VX4X2KCSMZcuWpU9Tfvjhh/SjfYw97V9oo7NZjuhu0OaeDS1HJIwzzzwzzUY4yhBAAGW4Mur/IKAZxe72L7QcafYvdLeobu7S/kWzHNGdoM1yRPdo7G45ok9MOPaeAALYe1b8yoNAQALQ/RrNcqS5uUt3imo5olmGbjHf03JESxNu8vrvABHAQWhqbajpb7raDn2pa+HChZ2+bAmh2b/QDV6abehHH6NykxcCOOjNO2nSpPjiiy/STUG1HZp+T548ufMS2F+ubd/k1XzhbU/XW1K6zAD2RD/z/9dHZxdeeGG88MILmUcuP1zN116ezr/PsKebvDRT0R7H3hwIYG8oVfJr9PXmBQsWxBVXXFHJFf//ZdZ87dXBbumCmQG0BFqneeONN2L69OlVTv9rvvYWI67uVAigxcguuOCC9JwDfVW5tmPq1KlpM63Ga6+NdZvXiwBapK1bafV0pHnz5rV41jyn0u2+5557brz22mt5BmSUThBAAC3FoD84M2bMSN/kq+3QtxV1h54erqKHonD0HwIIoKUsp0yZks60aNGils6Y7zSzZ89Of/Pr+wAc/YsAAmgpT33mO3/+/LjqqqtaOmO+02j6r83LuXPn5huUkTpBAAG0EMPMmTPjww8/TN/Vr+1g+l9bYvt2vQhg33jt16/WDTT6ptvHH3+8X7//YP6myy67LN2Lz/T/YKZQ7twIoBzbXSPXfAONpv/6Su5bb73VAilO0TYBBFCYeM030DD9L9wcHRgeARQOYdasWWn9X+MNNOz+F26ODgyPAAqHUPMXaNj9L9wcHRgeARQOodb1P9P/wo3RkeERQMEgal7/M/0v2BgdGhoBFAyj5vU/0/+CjdGhoRFAwTBqXf8z/S/YFB0bGgEUDKTW9b++tPTJJ59w80/B3ujK0AigUBI1r//1ajDdufjBBx8UosOwXSGAAAoloS/PfPXVV1V+/q/3B+qZhddff30hOgzbFQIIoFASzTvz3n777UJnKDOs3h+oa9fz+Dn6PwEEUChjvYjiqaeeiltuuaXQGcoMO2fOnHj66afTS0M5+j8BBFAgY72WWwLQCzR7e3sLnKHckBdffHEa/P333y93EkbuDAEEUCCK559/Pu68884kgNoOvXPvjjvuCM0EOPo/AQRQIOMbbrghFi9enF5RVduhF3HquvVJAEf/J4AACmSsTTS9Auzll18uMHq5IV955ZXQ3Yt6RRaHBwEEUCDnWjcAr7zyyvSxpT4J4PAggAAy51zzBqBmLuPGjePpP5l7osvDIYDM6dS8AVjrzCVzhFbDIYDMcde6AVjzzCVzhFbDIYDMcde6AVjzzCVzhFbDIYDMcdc6ja515pI5PrvhEEDGyGueRtc6c8kYn+VQCCBj7DVPo2uduWSMz3IoBJAxdr33b+nSpdXdAVjzzCVjfJZDIYCMsZ9zzjkxdOjQePfddzOOWn6ommcu5en07zMggIz5jho1Km699dZ46KGHMo5afig2AMsz7uoZEEDGZPQknZdeeimuvvrqjKOWH4oNwPKMu3oGBJAxmZ6enli/fn2MGDEi46jlh2IDsDzjrp4BAWRKRk/RnTJlSuzcuTPTiO0MwwZgO5y7ehYEkCkZPUbr/vvvj82bN2casZ1h2ABsh3NXz4IAMiVz2223xTvvvFPdU4Cvueaa+PLLL6v76DJTbPbDIIBMLXDJJZekkd57771MI7YzjJYtAwYMiI8++qidE3KWThFAAJni0GvALr300njmmWcyjdjOMGeccUZMnjw5XnzxxXZOyFk6RQABZIpjyJAh8fDDD6cHatZ06AEg1157bTzxxBM1XTbXmokAAsgEUtPoRYsWxXnnnZdpxHaGGT58eNxzzz1x9913t3NCztIpAgggQxwbNmyIkSNHRl9fX4bR2h1C9wDMnTs3brrppnZPzNk6QQABZIhh3rx5ceONN1b5NN1BgwbFm2++GVOnTs1AgiFqI4AAMiT2wAMPxLPPPhvr1q3LMFq7Q+g9AMuWLYvx48e3e2LO1gkCCCBDDDNnzoyVK1fGZ599lmG09obQC0C1d6G7FyUCDj8CCCBD5tOmTYtt27alTcCajhUrVsSECRN4E3BNoWW+VgSQAagEoGPhwoUZRmtvCF3v5ZdfHjt27GjvpJypUwQQQIY4ahWAbv6ZPXt2lS8xzRAbQ0QEAsjQBrUK4LHHHovHH388Nm7cmIECQ9RIAAFkSK1WAdx1113x6quvxqpVqzJQYIgaCSCADKnVKoCbb745Pv3001iyZEkGCgxRIwEEkCG1WgRw3333xSOPPLKrYt38o1eB1/bpRYbIGOL/CCCADK1QgwDuvffeePLJJ0NPAGqOSZMmxZgxY+L111/PQIEhaiSAADKkVoMAVKb+sJ9//vkxf/78VPXo0aNj1qxZ8eijj2agwBA1EkAAGVKrRQB6YrG+9KOXl+j5Bb29vfHcc8+FHgvO4UkAAWTIXQLQ04D1aK2uH5r261i8eHG6/beRQdevm+srQwABZOB6++23x4IFC2L16tUZRis7xPLly2PixInpASD6GFDfB+DwJYAAMmS/du3atL5es2ZNWld3/ZgxY0Z6duH27dv/tSnY9evm+vITQACZmI4dOzb94Z8+fXrMmTMn06jlhhk4cGAMHjw4tm7dWu4kjNx5AgggU0TXXXdduqtOx4MPPth5CehJQNoD2LJlSyYCDFMjAQSQMbXmb/4aZgDDhg1L6//aXmSSMS6G4stAvj0gAejYtGmTLwQq59uArj2AAFyT/3fdLAHoAwgYE0AAxuFTOgQQAD0AAWMCCMA4fEqHAAKgByBgTAABGIdP6RBAAPQABIwJIADj8CkdAgiAHoCAMQEEYBw+pUMAAdADEDAmgACMw6d0CCAAegACxgQQgHH4lA4BBEAPQMCYAAIwDp/SIYAA6AEIGBNAAMbhUzoEEAA9AAFjAgjAOHxKhwACoAcgYEwAARiHT+kQQAD0AASMCSAA4/ApHQIIgB6AgDEBBGAcPqVDAAHQAxAwJoAAjMOndAggAHoAAsYEEIBx+JQOAQRAD0DAmAACMA6f0iGAAOgBCBgTQADG4VM6BBAAPQABYwIIwDh8SocAAqAHIGBMAAEYh0/pEEAA9AAEjAkgAOPwKR0CCIAegIAxAQRgHD6lQwAB0AMQMCaAAIzDp3QIIAB6AALGBBCAcfiUDgEEQA9AwJgAAjAOn9IhgADoAQgYE0AAxuFTOgQQAD0AAWMCCMA4fEqHAAKgByBgTAABGIdP6RBAAPQABIwJIADj8CkdAv8B44DvecHNtZ0AAAAASUVORK5CYII='

    pillow_image = Image.open(io.BytesIO(base64.b64decode(img.split(',')[1])))
    src = np.array(pillow_image)
    processed = crop_and_resize(src)
    test = encode(processed)
