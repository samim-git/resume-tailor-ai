import { login, register } from '../../../app/api/auth'
import { setAccessToken } from '../../../shared/auth/tokenStore'

export async function loginAndStoreToken(username: string, password: string) {
  const data = await login({ username, password })
  setAccessToken(data.access_token)
  return data
}

export async function registerThenLogin(fullname: string, username: string, password: string) {
  await register({ fullname, username, password })
  return await loginAndStoreToken(username, password)
}

