#!/usr/bin/env python3
"""
Produce a message to an NSP (Nike Streaming Platform) Kafka topic.

All configuration is accepted via CLI args or environment variables.
Credentials (CLIENT_ID, CLIENT_SECRET) are env-var-only to avoid
leaking secrets in shell history.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests
from confluent_kafka import Producer


DEFAULT_TOKEN_URL = (
    "https://nike.okta.com/oauth2/aus27z7p76as9Dz0H1t7/v1/token"
)


class OAuthTokenProvider:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._token = None
        self._token_expiry = None

    def get_token(self):
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        print("Fetching OAuth token...")
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        token_data = response.json()
        self._token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
        print(f"Token obtained, expires in {expires_in}s")
        return self._token


_token_provider = None


def _oauth_token_callback(_config_str):
    token = _token_provider.get_token()
    return token, time.time() + 3600


def _delivery_report(err, msg):
    if err is not None:
        print(f"FAILED: {err}")
        sys.exit(1)
    else:
        print(
            f"Delivered to {msg.topic()} "
            f"[partition {msg.partition()}] "
            f"@ offset {msg.offset()}"
        )


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Produce a message to an NSP Kafka topic."
    )
    parser.add_argument(
        "--broker",
        default=os.environ.get("NSP_BROKER_URL"),
        help="NSP broker URL (or set NSP_BROKER_URL env var)",
    )
    parser.add_argument(
        "--topic",
        default=os.environ.get("NSP_TOPIC_NAME"),
        help="Full NSP topic name (or set NSP_TOPIC_NAME env var)",
    )
    parser.add_argument(
        "--token-url",
        default=os.environ.get("NSP_TOKEN_URL", DEFAULT_TOKEN_URL),
        help="Okta OAuth token URL (default: Nike Okta endpoint)",
    )
    parser.add_argument(
        "--payload",
        required=True,
        help="Path to JSON payload file, or '-' for stdin",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Optional message key",
    )
    return parser.parse_args()


def main():
    global _token_provider

    args = _parse_args()

    if not args.broker:
        print("ERROR: --broker or NSP_BROKER_URL is required.")
        sys.exit(1)
    if not args.topic:
        print("ERROR: --topic or NSP_TOPIC_NAME is required.")
        sys.exit(1)

    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    if not client_id or not client_secret:
        print("ERROR: CLIENT_ID and CLIENT_SECRET environment variables are required.")
        print("  export CLIENT_ID='...'")
        print("  export CLIENT_SECRET='...'")
        sys.exit(1)

    if args.payload == "-":
        payload_raw = sys.stdin.read()
    else:
        with open(args.payload) as f:
            payload_raw = f.read()

    try:
        payload = json.dumps(json.loads(payload_raw))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON payload: {e}")
        sys.exit(1)

    print(f"Broker:  {args.broker}")
    print(f"Topic:   {args.topic}")
    print(f"Key:     {args.key or '(none)'}")
    print(f"Payload: {len(payload)} bytes")
    print()

    _token_provider = OAuthTokenProvider(client_id, client_secret, args.token_url)
    try:
        _token_provider.get_token()
        print("OAuth authentication successful")
    except Exception as e:
        print(f"OAuth authentication failed: {e}")
        sys.exit(1)

    producer = Producer({
        "bootstrap.servers": args.broker,
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "OAUTHBEARER",
        "oauth_cb": _oauth_token_callback,
        "acks": "all",
        "retries": 3,
        "retry.backoff.ms": 1000,
    })

    print("Producing message...")
    produce_kwargs = {
        "topic": args.topic,
        "value": payload.encode("utf-8"),
        "callback": _delivery_report,
    }
    if args.key:
        produce_kwargs["key"] = args.key.encode("utf-8")

    producer.produce(**produce_kwargs)

    remaining = producer.flush(timeout=30)
    if remaining > 0:
        print(f"WARNING: {remaining} messages not delivered")
        sys.exit(1)
    else:
        print("Done.")


if __name__ == "__main__":
    main()
