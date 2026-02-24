from src.notify.base import BaseNotifier


def get_notifier_templates():
    default_message_template = BaseNotifier.DEFAULT_TEMPLATE
    message_template_help = (
        "支持模板字符串，以下为可用变量:\n"
        "{title}: 商品标题\n"
        "{price}: 商品价格\n"
        "{image}: 商品图片\n"
        "{origin_price}: 商品原价\n"
        "{location}: 发货地址\n"
        "{score}: 推荐度\n"
        "{reason}: AI 分析结果\n"
        "{link}: 商品链接"
    )

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
                },
                'message_template': {
                    'name': '消息模板',
                    'type': 'textarea',
                    'placeholder': '留空使用默认模板',
                    'default': (
                        '售价：{price}（原价：{origin_price}）\n'
                        '发货地：{location} \n'
                        'AI分析：{reason} \n'
                    ),
                    'help': message_template_help,
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
                },
                'message_template': {
                    'name': '消息模板',
                    'type': 'textarea',
                    'placeholder': '留空使用默认模板',
                    'default': default_message_template,
                    'help': message_template_help,
                }
            },
            'doc': 'https://gotify.net/docs/index'
        },
        {
            'id': '2',
            'type': 'wechat',
            'name': '企业微信机器人(Webhook)',
            'template': {
                'key': {
                    'name': 'key',
                    'type': 'password',
                    'required': True,
                },
                'message_template': {
                    'name': '消息模板',
                    'type': 'textarea',
                    'placeholder': '留空使用默认模板',
                    'default': default_message_template,
                    'help': message_template_help,
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
                },
                'message_template': {
                    'name': '消息模板',
                    'type': 'textarea',
                    'placeholder': '留空使用默认模板',
                    'default': default_message_template,
                    'help': message_template_help,
                }
            },
            'doc': 'https://sctapi.ftqq.com/'
        },
        {
            'id': '4',
            'type': 'webhook',
            'name': '通用 Webhook',
            'template': {
                'url': {
                    'name': 'Webhook 地址',
                    'type': 'url',
                    'required': True,
                },
                'headers': {
                    'name': '自定义 Headers',
                    'type': 'textarea',
                    'rows': 3,
                    'placeholder': 'JSON 格式，例如: {"Authorization": "Bearer xxx"}',
                    'help': 'JSON 格式的自定义请求头，留空不设置',
                },
                'message_template': {
                    'name': '消息模板',
                    'type': 'textarea',
                    'placeholder': '留空使用默认模板',
                    'default': default_message_template,
                    'help': message_template_help,
                }
            },
        }
    ]
