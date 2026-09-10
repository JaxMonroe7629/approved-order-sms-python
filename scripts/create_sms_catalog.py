import argparse
import json

from order_sms.infrai_sms import InfraiSms
from order_sms.template_catalog import create_catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--signature", required=True)
    args = parser.parse_args()
    result = create_catalog(InfraiSms(), args.namespace, args.signature)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

