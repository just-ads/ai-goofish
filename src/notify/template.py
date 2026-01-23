def get_notifier_templates():
    return [
        {
            'id': '0',
            'type': 'ntfy',
            'name': 'ntfy',
            'template': {
                'url': {
                    'name': '通知地址',
                    'type': 'url',
                }
            },
            'doc': 'https://docs.ntfy.sh/'
        },
        {
            'id': '1',
            'type': 'gotify',
            'name': 'gotify',
            'template': {
                'url': {
                    'name': '通知地址',
                    'type': 'url',
                },
                'token': {
                    'name': 'token',
                    'type': 'password',
                }
            },
            'doc': 'https://gotify.net/docs/index'
        },
        {
            'id': '2',
            'type': 'webchat',
            'name': '企业微信机器人(Webhook)',
            'template': {
                'url': {
                    'name': 'Webhook 地址',
                    'type': 'url',
                }
            },
            'doc': 'https://developer.work.weixin.qq.com/document/path/99110'
        }
    ]

