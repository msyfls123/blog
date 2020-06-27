---
title: 格式化与验证
date: 2020-06-27 22:12:41
tags:
categories: web
thumbnail: images/format-and-validate-1.png
disqusId: format-and-validate
---

众所周知，前端很大程度上就是做数据的展示和收集工作，这时候用户看到的内容和服务端存储的数据中间就会有多层转换过程。

# 钱

最重要的当然是 money 啦，相差一分钱都能让用户急得哇哇大叫。比如业务里有三种价格：
- `fixed_price` 原价
- `promotion_price` 特价，一般为 `fixed_price * promotion.discount`
- `vip_price` 会员价，一般为 `fixed_price * vip.discount`，可能为空

经常出现的情形时既要显示折扣（`discount`）又要显示价格（promotion_price or vip_price），可不可以直接返回 `fixed_price` 和 `discount` 呢？不可以！细心的读者已经觉察到问题了 —— `discount` `为小数，fixed_price` 与其相乘很可能不是一个整数（这里要插一句，一般情况下价格都是记录为 int，以 cent 作为单位）。比如臭名昭著的 `JavaScript` 浮点数相加问题。

```
> 0.1 + 0.2
< 0.30000000000000004
> 0.1 + 0.2 === 0.3
< false
```

原因就是 float 在计算机里存了 32 位，1 位符号位 + 8 位指数位 + 23 位尾数，反正就是不精确就完事了。那我们即使不精确也要保证各处拿到的是一个值，这个值只能以后端为准。

```python
@property
def promotion_price(self):
  promotion = self.get_active_promotion()
    if not promotion:
        return self.fixed_price

    if self.is_chapter:
        return int(self.fixed_price * self.column.promotion_discount)
    return promotion.price
```

这个值是惰性的，也就是说只有用到时才会计算值，返回的一定是一个整数。有一些应用场景：

- 直接展示价格：`(price / 100).toFixed(2)` => `0.99`
- 很多章节合并购买，`items.reduce((total, item) => total + item.price, 0)` 注意这个值可能会不等于整本的定价，这时就要引导或劝说用户直接买整本更划算呀
- 满减活动，类似合并购买情形，只不过是有一些阈值情形
  ```javascript
  getMaxAvailableRebateAmountInGroup = (group) => {
    const total = this.getTotalPriceInGroup(group)
    let maxAmount = 0

    if (!group.event) {
      return maxAmount
    }

    group.event.availablecouponGroups.some((coupon) => {
      if (total > coupon[0]) {
        maxAmount = coupon[1]
      }
      return total > coupon[0]
    })
    return maxAmount
  }
  /**
   * Returns rebate threshold info.
   * @param {Object[]} couponGroups - Available coupons.
   * @param {number} couponGroups[][0] - The threshold of coupon.
   * @param {number} couponGroups[][1] - The amount of coupon, will be reduced from price when total meets threshold.
   * @param {numer} total - Total of prices.
   * @returns {[string, bool]} Description String, isMaxThresholdMet
   */
  // returned value: [descString, isMaxThresholdMet]
  getRebateThreshold = (couponGroups, total) => {
    const mf = moneyformatShort
    

    if (couponGroups.length === 0 ) {
      return ['本活动满减券已全部用完', true]
    }

    for (let i = 0, prev_threshold = 0, prev_amount = 0; i < couponGroups.length; i++) {
      const [threshold, amount] = couponGroups[i]

      if (total >= threshold) {
        if (i === 0) {
          return ['已购满 ' + mf(threshold) + '，已减 ' + mf(amount), true]
        } else {
          return ['已减 ' + mf(amount) +
            '，再购 ' + mf(prev_threshold - total) + ' 可减 ' + mf(prev_amount), false]
        }
      } else {
        if (i === couponGroups.length - 1) {
          return ['购满 ' + mf(threshold) + ' 可减 ' + mf(amount) +
            '，还差 ' + mf(threshold - total), false]
        }
      }
      [prev_threshold, prev_amount] = [threshold, amount]
    }
  }

  getTotalPriceInGroup = (group) => {
    return group.itemList.reduce((total, item) => {
      if (item.onSale && item.selected) {
        total += item.salePrice
      }
      return total
    }, 0)
  }
  ```

钱的计算大概就是这样，涉及到第三方支付就更头疼了。

# 时间

金钱是宝贵的，时间是更宝贵的。而我们需要根据不同场景甚至用户所在时区去显示不同的时间格式，有一种方案是 `date-fns`，项目里也有根据 timestamp 转换成用户可读格式的各种函数，但有时候只是想简简单单显示一个时间，同时考虑各种情况下的复用性。上 `GraphQL`！

```python
import time
from libs.utils.date import mtimeformat
from ..types import TimeFormat

def format_time(time_, format=TimeFormat.FULL_TIME.value):
    return {
        TimeFormat.FURTHER: mtimeformat(time_),
        TimeFormat.FULL_TIME: time_.strftime('%Y-%m-%d %H:%M:%S'),
        TimeFormat.FULL_DAY: time_.strftime('%Y-%m-%d'),
        TimeFormat.CHINESE_FULL_DAY: time_.strftime('%Y 年 %-m 月 %-d 日'),
        TimeFormat.ISO: time_.isoformat(),
        TimeFormat.TIMESTAMP: int(time.mktime(time_.timetuple()) * 1000),
    }[format]
```

其中 `TimeFormat` 是一个 `GraphQL` 的 enum 类型，`mtimeformat` 是一个可以根据相差时间来区别展示的函数，比如可以展示成「刚刚」「5 分钟前」这样的口语化格式。

![实际效果](/blog/images/format-and-validate-2.png)

# 表单

表单的验证可以有很多实现，最简单的莫过于 `maxlength` 及 `require` 这种，直接交给浏览器，项目里也用到了一些 `jQuery` 的表单绑定，在提交之前一次性遍历表单项根据 `data-*` 来进行 check。

现实是 react 相关的表单验证有以下两个痛点：

## 异步验证

所幸的是 `formik` 支持了 `Promise` 的验证结果

```jsx
<Field name={name} type="number"
  validate={function(value) {
    return fetchAgent(value).then((res) => {
      if (res.agentExisted) {
        if (res.existed) {
          return `该作者经纪合同已经存在，负责人：${res.editorName}`
        }
      } else {
        return `'作者 ID' 为 ${value} 的用户不存在或不是作者身份`
      }
    })
  }}
/>
```

## 依赖另一输入
```typescript
import * as Yup from 'yup'

const OTHER_NATIONALITY = '其他'

export const validationSchema=Yup.object().shape({
  nationality: Yup.string().nullable(true).required('请选择国家或地区'),
  otherNationality: Yup.string().test(
    'need-other-nationality',
    '请填写其他国家或地区',
    function(value) {
      return this.parent.nationality !== OTHER_NATIONALITY || !!value
    }
  ),
})
```

![实际情形为中间的输入框依赖于前面的下拉筛选框是否选了「其他」](/blog/images/format-and-validate-3.png)

# 路由

异步鉴权路由

```jsx
const PrivateRoute = ({ component: Component, ...rest }) => {
  const user = useSelector(state => selectors.user(state))
  const isLoaded = useSelector(state => selectors.isLoaded(state))

  return (
    <Route
      {...rest}
      render={(props) =>
        !isLoaded ? (
          <></>
        ) : user ? (
          <Component {...props} />
        ) : (
          <Redirect to='/404' />
        )
      }
    />
  )
}
```
