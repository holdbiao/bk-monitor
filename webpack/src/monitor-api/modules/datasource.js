import { request } from '../base'

export const asyncTesting = request('GET', 'rest/v1/async_testing/')

export default {
  asyncTesting
}
