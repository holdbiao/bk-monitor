<template>
  <article class="import-configuration-upload">
    <section class="upload">
      <upload
        action="rest/v2/export_import/upload_package/"
        :on-upload-success="handleSuccess"
        :on-upload-error="handleError"
        :headers="headers"
      ></upload>
    </section>
  </article>
</template>
<script>
import Upload from '../components/upload'
import { getCookie } from '../../../../monitor-common/utils/utils'

export default {
  name: 'ImportConfigurationUpload',
  components: {
    Upload
  },
  data() {
    return {
      headers: [
        {
          name: 'X-Requested-With',
          value: 'XMLHttpRequest'
        },
        {
          name: 'X-CSRFToken',
          value: getCookie(this.$store.getters.csrfCookieName)
        }
      ]
    }
  },
  created() {

  },
  methods: {
    handleSuccess(res) {
      this.$router.push({
        name: 'import-configuration',
        params: {
          importData: res.data
        }
      })
    },
    handleError(err) {
      console.log(err)
    }
  }
}
</script>
<style lang="scss" scoped>
    .upload {
      display: flex;
      justify-content: center;
      margin-top: 74px;
    }
</style>
