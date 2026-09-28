import request from './request'

// 添加体重记录
export function addWeight(data) {
  return request({
    url: '/weight/add',
    method: 'post',
    data
  })
}

// 体重记录列表 type=day|week|month
export function listWeight(params) {
  return request({
    url: '/weight/list',
    method: 'get',
    params
  })
}

// 删除体重记录
export function deleteWeight(id) {
  return request({
    url: '/weight/' + id,
    method: 'delete'
  })
}
