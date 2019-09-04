import googleapiclient.discovery


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
