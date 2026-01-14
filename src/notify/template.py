def get_notifier_template():
    return [
        {
            'type': 'ntfy',
            'template': {
                'url': '通知地址'
            },
            'doc': 'https://docs.ntfy.sh/'
        },
        {
            'type': 'gotify',
            'template': {
                'url': '通知地址',
                'token': 'token'
            },
            'doc': 'https://gotify.net/docs/index'
        }
    ]
