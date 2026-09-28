import {randomUUID} from 'node:crypto';
import {MAX_IMAGE_BYTES, IMAGE_TYPES, validateImageFile} from './image-policy.mjs';

// Inspect bytes as well as browser metadata; SVG/HTML and renamed files are rejected.
export function decodeImage(input) {
  if (typeof input.data !== 'string' || input.data.length > 4 * Math.ceil(MAX_IMAGE_BYTES / 3) ||
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(input.data))
    throw new Error('이미지 데이터가 올바르지 않거나 3MB를 초과했습니다.');
  const bytes = Buffer.from(input.data, 'base64');
  validateImageFile({name:input.name, type:input.type, size:bytes.length});
  const signature = bytes.subarray(0, 12);
  const detected = signature[0] === 0xff && signature[1] === 0xd8 && signature[2] === 0xff ? 'image/jpeg'
    : signature.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) ? 'image/png'
    : signature.subarray(0, 4).toString() === 'RIFF' && signature.subarray(8, 12).toString() === 'WEBP' ? 'image/webp' : '';
  if (detected !== input.type) throw new Error('파일 내용이 JPG, PNG, WebP 형식과 일치하지 않습니다.');
  return bytes;
}

export async function storeImage(input, environment, putBlob) {
  let bytes;
  try { bytes = decodeImage(input); }
  catch (error) { error.status = 400; throw error; }
  // A dedicated variable wins; an existing default Blob token is never overwritten.
  const token = environment.MODU_IMAGE_BLOB_READ_WRITE_TOKEN || environment.BLOB_READ_WRITE_TOKEN;
  if (!token) {
    const error = new Error('이미지 저장소가 연결되지 않았습니다. Vercel Blob 연결과 환경변수를 확인해 주세요. 기존 이미지 주소 입력은 계속 사용할 수 있습니다.');
    error.status = 503; throw error;
  }
  const scope = environment.VERCEL_ENV === 'production' ? 'production' : environment.VERCEL_ENV === 'preview' ? 'preview' : 'development';
  const pathname = `modu-today/images/${scope}/${randomUUID()}.${IMAGE_TYPES[input.type]}`;
  try {
    const put = putBlob || (await import('@vercel/blob')).put;
    const blob = await put(pathname, bytes, {
      access:'public', token, contentType:input.type, addRandomSuffix:false,
      allowOverwrite:false, abortSignal:AbortSignal.timeout(30000)
    });
    const url = new URL(blob.url);
    if (url.protocol !== 'https:' || !url.hostname.endsWith('.public.blob.vercel-storage.com') || url.username || url.password)
      throw new Error('Unexpected storage response');
    return {url:url.href, contentType:input.type, size:bytes.length};
  } catch {
    const error = new Error('이미지 업로드에 실패했습니다. 저장소 연결·용량 또는 네트워크를 확인한 뒤 다시 선택해 주세요.');
    error.status = 502; throw error;
  }
}
