import Vue from 'vue'
import Vuex from 'vuex'
import App, { IAppState } from './modules/app'

Vue.use(Vuex)

export interface IRootState {
  app: IAppState;
}

export default new Vuex.Store<IRootState>({
  modules: {
    app: App
  },
  strict: process.env.NODE_ENV !== 'production'
})
