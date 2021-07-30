import MiniCssExtractPlugin from 'mini-css-extract-plugin'

export default (isProd: boolean) => {
  const cssLoaders = [
    isProd
      ? {
        loader: MiniCssExtractPlugin.loader
      } : 'vue-style-loader',,
    {
      loader: 'css-loader',
      options: {
        esModule: false,
        sourceMap: !isProd
      }
    },
    isProd ?
    {
      loader: 'postcss-loader',
      options: {
        postcssOptions: {
          plugins: [
            [
              'postcss-preset-env',
              {
                flexbox: 'no-2009',
                grid: true
              }
            ],
            'postcss-flexbugs-fixes'
          ]
        }
      }
    } : undefined
  ].filter(Boolean)
  return [
    {
      test: /\.css$/,
      use: [
        ...cssLoaders
      ].filter(Boolean)
    },
    {
      test: /\.scss$/,
      use: [
        ...cssLoaders,
        'sass-loader'
      ].filter(Boolean)
    }
  ]
}
