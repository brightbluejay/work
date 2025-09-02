#!/usr/bin/env python3
"""
List EC2 instances and SSM-managed EC2 instances per region,
then print EC2 instances not managed by SSM.

Usage:
  python ec2_ssm_audit.py [--profile PROFILE] [--regions eu-west-2,eu-west-1] [--include-stopped]

Notes:
  - Filters out terminated/shutting-down EC2 by default.
  - Filters SSM to ResourceType=EC2Instance (excludes hybrid 'mi-*' nodes).
"""

import argparse
import sys
from typing import List, Set, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


def session_from_args(profile: str | None):
    try:
        return boto3.Session(profile_name=profile) if profile else boto3.Session()
    except (BotoCoreError, NoCredentialsError) as e:
        print(f"[FATAL] Failed to create session: {e}", file=sys.stderr)
        sys.exit(1)


def list_regions(sess: boto3.Session, explicit: List[str] | None) -> List[str]:
    if explicit:
        return explicit
    ec2 = sess.client("ec2")
    try:
        resp = ec2.describe_regions(AllRegions=False)
        return sorted(r["RegionName"] for r in resp.get("Regions", []))
    except (ClientError, BotoCoreError) as e:
        print(f"[ERROR] describe_regions failed: {e}", file=sys.stderr)
        # Fallback to session region if available
        if sess.region_name:
            return [sess.region_name]
        sys.exit(1)


def get_ec2_instances(sess: boto3.Session, region: str, include_stopped: bool = False) -> Set[str]:
    ec2 = sess.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instances")
    filters = [
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"] if include_stopped else ["pending", "running"]}
    ]
    ids: Set[str] = set()
    try:
        for page in paginator.paginate(Filters=filters):
            for res in page.get("Reservations", []):
                for inst in res.get("Instances", []):
                    iid = inst.get("InstanceId")
                    if iid:
                        ids.add(iid)
    except (ClientError, BotoCoreError) as e:
        print(f"[WARN] ({region}) Failed to get EC2 instances: {e}", file=sys.stderr)
    return ids


def get_ssm_ec2_instances(sess: boto3.Session, region: str) -> Set[str]:
    ssm = sess.client("ssm", region_name=region)
    paginator = ssm.get_paginator("describe_instance_information")
    ids: Set[str] = set()
    try:
        for page in paginator.paginate(Filters=[{"Key": "ResourceType", "Values": ["EC2Instance"]}]):
            for info in page.get("InstanceInformationList", []):
                iid = info.get("InstanceId")
                # SSM returns i-... for EC2 and mi-... for hybrid; filter above ensures EC2 only
                if iid and iid.startswith("i-"):
                    ids.add(iid)
    except (ClientError, BotoCoreError) as e:
        print(f"[WARN] ({region}) Failed to get SSM instances: {e}", file=sys.stderr)
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="AWS profile to use")
    parser.add_argument("--regions", help="Comma-separated regions to scan (default: all enabled regions)")
    parser.add_argument("--include-stopped", action="store_true", help="Include stopped EC2 instances")
    args = parser.parse_args()

    sess = session_from_args(args.profile)
    explicit_regions = [r.strip() for r in args.regions.split(",")] if args.regions else None
    regions = list_regions(sess, explicit_regions)

    summary: Dict[str, Dict[str, int]] = {}
    unmanaged_total: int = 0

    for region in regions:
        ec2_ids = get_ec2_instances(sess, region, include_stopped=args.include_stopped)
        ssm_ids = get_ssm_ec2_instances(sess, region)
        unmanaged = sorted(ec2_ids - ssm_ids)

        print(f"\n=== {region} ===")
        print(f"EC2 instances: {len(ec2_ids)}")
        print(f"SSM-managed EC2: {len(ssm_ids)}")
        print("Unmanaged EC2 instances:")
        if unmanaged:
            for iid in unmanaged:
                print(f"  - {iid}")
        else:
            print("  (none)")

        summary[region] = {
            "ec2": len(ec2_ids),
            "ssm": len(ssm_ids),
            "unmanaged": len(unmanaged),
        }
        unmanaged_total += len(unmanaged)

    print("\n=== Summary ===")
    for region in regions:
        s = summary[region]
        print(f"{region}: EC2={s['ec2']}, SSM={s['ssm']}, Unmanaged={s['unmanaged']}")
    print(f"Total unmanaged across regions: {unmanaged_total}")


if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError:
            print("[FATAL] No AWS credentials found. Configure SSO/profile and try again.", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
