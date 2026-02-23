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
                    'required': True,
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
                    'required': True,
                },
                'token': {
                    'name': 'token',
                    'type': 'password',
                    'required': True,
                }
            },
            'doc': 'https://gotify.net/docs/index'
        },
        {
            'id': '2',
            'type': 'wechat',
            'name': '企业微信机器人(Webhook)',
            'template': {
                'url': {
                    'name': 'Webhook 地址',
                    'type': 'url',
                    'default': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
                    'editable': False,
                },
                'key': {
                    'name': 'key',
                    'type': 'password',
                    'required': True,
                }
            },
            'doc': 'https://developer.work.weixin.qq.com/document/path/99110'
        },
        {
            'id': '3',
            'type': 'serverchan',
            'name': 'Server酱',
            'template': {
                'sendkey': {
                    'name': 'SendKey',
                    'type': 'password',
                    'required': True,
                },
                'noip': {
                    'name': '隐藏调用IP',
                    'type': 'switch',
                    'checkedLabel': '隐藏',
                    'uncheckedLabel': '显示',
                },
                'channel': {
                    'name': '消息通道',
                    'type': 'select',
                    'multiple': True,
                    'placeholder': '留空使用默认通道',
                    'options': [
                        {'label': '方糖服务号', 'value': '9'},
                        {'label': '企业微信应用消息', 'value': '66'},
                        {'label': '企业微信群机器人', 'value': '1'},
                        {'label': '钉钉群机器人', 'value': '2'},
                        {'label': '飞书群机器人', 'value': '3'},
                        {'label': 'Bark iOS', 'value': '8'},
                        {'label': '测试号', 'value': '0'},
                        {'label': 'PushDeer', 'value': '18'},
                        {'label': '自定义', 'value': '88'},
                        {'label': '官方Android版·β', 'value': '98'},
                    ],
                },
                'openid': {
                    'name': '消息抄送OpenID',
                    'type': 'text',
                    'placeholder': '多个用逗号隔开，留空不抄送',
                }
            },
            'doc': 'https://sctapi.ftqq.com/'
        }
    ]
