import { Component, Vue } from 'vue-property-decorator'

@Component
export default class documentLinkMixin extends Vue {
  public aggConditionColorMap: {
    'AND': '#3A84FF',
    'OR': '#3A84FF',
    '=': '#FF9C01',
    '>': '#FF9C01',
    '<': '#FF9C01',
    '<=': '#FF9C01',
    '>=': '#FF9C01',
    '!=': '#FF9C01',
    'like': '#FF9C01',
    'between': '#FF9C01',
    'is': '#FF9C01',
    'is one of': '#FF9C01',
    'is not': '#FF9C01',
    'is not one of': '#FF9C01',
    'include': '#FF9C01',
    'exclude': '#FF9C01',
    'reg': '#FF9C01'
  }
  public aggConditionFontMap: {
    '=': 'bold',
    '>': 'bold',
    '<': 'bold',
    '<=': 'bold',
    '>=': 'bold',
    '!=': 'bold',
    'like': 'bold',
    'between': 'bold',
    'include': 'bold',
    'exclude': 'bold',
    'reg': 'bold'
  }
  public methodMap: {
    'gte': '>=',
    'gt': '>',
    'lte': '<=',
    'lt': '<',
    'eq': '=',
    'neq': '!=',
    'like': 'like',
    'between': 'between',
    'is': 'is',
    'is one of': 'is one of',
    'is not': 'is not',
    'is not one of': 'is not one of',
    'include': 'include',
    'exclude': 'exclude',
    'reg': 'regex'
  }
}
