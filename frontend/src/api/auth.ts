import { request } from './request'

// 登录
export const login = (data: { username: string; password: string }) => {
  return request.post('/v1/auth/login', data)
}

// 注册
export const register = (data: { 
  username: string
  email: string
  password: string
  full_name?: string 
}) => {
  return request.post('/v1/auth/register', data)
}

// 获取用户信息
export const getUserInfo = () => {
  return request.get('/v1/user/me')
}

// 更新用户信息
export const updateUserInfo = (data: {
  full_name?: string
  phone?: string
  avatar?: string
  preferences?: object
}) => {
  return request.put('/v1/user/me', data)
}

// 修改密码
export const updatePassword = (data: {
  old_password: string
  new_password: string
}) => {
  return request.put('/v1/user/me/password', data)
}

// 刷新token
export const refreshToken = (refresh_token: string) => {
  return request.post('/v1/auth/refresh', { refresh_token })
}

// 退出登录
export const logout = (refresh_token?: string) => {
  return request.post('/v1/auth/logout', { refresh_token })
}
