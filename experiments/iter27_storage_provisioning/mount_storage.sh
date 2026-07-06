#!/usr/bin/env bash
set -euo pipefail

PRIMARY_DISK_BY_ID=/dev/disk/by-id/google-sentinel-nuscenes-data-1tb
ATTACHED_DISK_BY_ID=/dev/disk/by-id/google-persistent-disk-1
MOUNT_POINT=/datasets/nuscenes-full

if test -e "${PRIMARY_DISK_BY_ID}"; then
  DISK_BY_ID="${PRIMARY_DISK_BY_ID}"
elif test -e "${ATTACHED_DISK_BY_ID}"; then
  DISK_BY_ID="${ATTACHED_DISK_BY_ID}"
else
  echo "ITER27_DISK_BY_ID_MISSING"
  exit 1
fi

echo "ITER27_DISK_BY_ID ${DISK_BY_ID}"
mkdir -p "${MOUNT_POINT}"

if blkid "${DISK_BY_ID}" >/dev/null 2>&1; then
  echo "ITER27_EXISTING_FILESYSTEM"
else
  echo "ITER27_FORMAT_EMPTY_DISK"
  mkfs.ext4 -F -L sentinel-nuscenes "${DISK_BY_ID}"
fi

UUID="$(blkid -s UUID -o value "${DISK_BY_ID}")"
if mountpoint -q "${MOUNT_POINT}"; then
  echo "ITER27_ALREADY_MOUNTED"
else
  mount "UUID=${UUID}" "${MOUNT_POINT}"
  echo "ITER27_MOUNTED"
fi

if grep -q "${UUID}" /etc/fstab; then
  echo "ITER27_FSTAB_PRESENT"
else
  printf "UUID=%s %s ext4 defaults,nofail 0 2\n" "${UUID}" "${MOUNT_POINT}" >> /etc/fstab
  echo "ITER27_FSTAB_ADDED"
fi

echo "ITER27_DF_BYTES"
df -B1 "${MOUNT_POINT}"
echo "ITER27_DF_HUMAN"
df -h "${MOUNT_POINT}"
echo "ITER27_LSBLK"
lsblk -f
echo "ITER27_BLKID"
blkid "${DISK_BY_ID}"
echo "ITER27_FSTAB_LINE"
grep "${UUID}" /etc/fstab
echo "ITER27_DOCKER_PS"
docker ps --format "{{.Names}}"
