export interface IRule {
  name: boolean,
  scenario: boolean,
  nameTips: string
}

export interface IFormData {
  bkEventGroupId: string,
  bkDataId: string,
  name: string,
  scenario: string,
  token: string
}

export interface IParams {
  'bk_event_group_id'?: string,
  'time_series_group_id'?: string
}
