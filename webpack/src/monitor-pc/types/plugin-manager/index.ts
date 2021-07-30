export interface ISystem {
  name: string,
  enable: boolean
  languageList: ILanguage[]
}
export interface ILanguage {
  name: string,
  lang: string,
  text: string,
  abb: string,
  active: boolean
}
export interface IValues {
  name: {
    lang: string,
    text: string
  }
}
