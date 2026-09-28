export const MAX_IMAGE_BYTES = 3 * 1024 * 1024;
export const MAX_IMAGE_REQUEST_BYTES = 4 * Math.ceil(MAX_IMAGE_BYTES / 3) + 4096;
export const IMAGE_TYPES = {'image/jpeg':'jpg', 'image/png':'png', 'image/webp':'webp'};

export function validateImageFile({name, type, size}) {
  if (!Object.hasOwn(IMAGE_TYPES, type) || typeof name !== 'string' || name.length > 255 ||
      !/\.(jpe?g|png|webp)$/i.test(name))
    throw new Error('JPG, PNG, WebP 이미지 파일만 업로드할 수 있습니다.');
  const extension = name.split('.').pop().toLowerCase().replace('jpeg', 'jpg');
  if (extension !== IMAGE_TYPES[type]) throw new Error('파일 확장자와 이미지 형식이 일치하지 않습니다.');
  if (!Number.isInteger(size) || size < 1) throw new Error('빈 이미지 파일은 업로드할 수 없습니다.');
  if (size > MAX_IMAGE_BYTES) throw new Error('이미지는 파일당 3MB 이하로 선택해 주세요.');
}
