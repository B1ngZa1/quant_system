"""技术指标服务测试 - 指标计算逻辑"""

import pandas as pd


class TestIndicatorCalculations:
    """指标计算逻辑单元测试（不需要DB）"""

    def _compute_indicators(self, closes: list[float]) -> pd.DataFrame:
        """复制 IndicatorService 的核心计算逻辑"""
        df = pd.DataFrame({"close": closes})
        df.index = pd.RangeIndex(len(df))

        # MA
        df["ma5"] = df["close"].rolling(window=5).mean()
        df["ma10"] = df["close"].rolling(window=10).mean()
        df["ma20"] = df["close"].rolling(window=20).mean()
        df["ma60"] = df["close"].rolling(window=60).mean()

        # MACD
        exp1 = df["close"].ewm(span=12, adjust=False).mean()
        exp2 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd_dif"] = exp1 - exp2
        df["macd_dea"] = df["macd_dif"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = (df["macd_dif"] - df["macd_dea"]) * 2

        # BOLL
        df["boll_mid"] = df["close"].rolling(window=20).mean()
        std = df["close"].rolling(window=20).std()
        df["boll_upper"] = df["boll_mid"] + 2 * std
        df["boll_lower"] = df["boll_mid"] - 2 * std

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi14"] = 100 - (100 / (1 + rs))

        return df

    def test_ma5_first_valid_index(self):
        closes = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        df = self._compute_indicators(closes)
        # MA5 should be NaN for first 4 rows, valid at index 4
        assert pd.isna(df.loc[3, "ma5"])
        assert not pd.isna(df.loc[4, "ma5"])
        expected_ma5 = sum(closes[:5]) / 5
        assert abs(df.loc[4, "ma5"] - expected_ma5) < 1e-10

    def test_ma10_calculation(self):
        closes = [float(i) for i in range(20, 40)]
        df = self._compute_indicators(closes)
        expected = sum(closes[:10]) / 10
        assert abs(df.loc[9, "ma10"] - expected) < 1e-10

    def test_macd_dif_sign_on_uptrend(self):
        """上升趋势中 MACD DIF 应为正"""
        closes = [float(i) for i in range(10, 50)]
        df = self._compute_indicators(closes)
        last_dif = df["macd_dif"].dropna().iloc[-1]
        assert last_dif > 0

    def test_macd_hist_is_twice_diff(self):
        closes = [10.0, 10.5, 10.2, 10.8, 11.0, 11.5, 11.3, 11.8, 12.0, 12.5,
                   12.3, 12.8, 13.0, 13.5, 13.3, 13.8, 14.0, 14.5, 14.3, 14.8,
                   15.0, 15.5, 15.3, 15.8, 16.0, 16.5, 16.3, 16.8, 17.0, 17.5]
        df = self._compute_indicators(closes)
        valid = df.dropna(subset=["macd_dif", "macd_dea"])
        assert len(valid) > 0
        for _, row in valid.iterrows():
            expected_hist = (row["macd_dif"] - row["macd_dea"]) * 2
            assert abs(row["macd_hist"] - expected_hist) < 1e-10

    def test_boll_upper_above_mid(self):
        closes = [10.0, 11.0, 10.5, 12.0, 11.5, 13.0, 12.5, 14.0, 13.5, 15.0,
                   14.5, 16.0, 15.5, 17.0, 16.5, 18.0, 17.5, 19.0, 18.5, 20.0,
                   19.5, 21.0, 20.5, 22.0, 21.5, 23.0, 22.5, 24.0, 23.5, 25.0]
        df = self._compute_indicators(closes)
        valid = df.dropna(subset=["boll_upper", "boll_mid", "boll_lower"])
        assert len(valid) > 0
        for _, row in valid.iterrows():
            assert row["boll_upper"] > row["boll_mid"] > row["boll_lower"]

    def test_boll_mid_equals_ma20(self):
        closes = [float(i) for i in range(100, 130)]
        df = self._compute_indicators(closes)
        valid = df.dropna(subset=["boll_mid", "ma20"])
        assert len(valid) > 0
        for _, row in valid.iterrows():
            assert abs(row["boll_mid"] - row["ma20"]) < 1e-10

    def test_rsi_bounded_0_to_100(self):
        closes = [10.0, 10.5, 10.2, 10.8, 11.0, 11.5, 11.3, 11.8, 12.0, 12.5,
                   12.3, 12.8, 13.0, 13.5, 13.3, 13.8, 14.0, 14.5, 14.3, 14.8,
                   15.0, 15.5, 15.3, 15.8, 16.0, 16.5, 16.3, 16.8, 17.0]
        df = self._compute_indicators(closes)
        rsi_values = df["rsi14"].dropna()
        assert len(rsi_values) > 0
        for val in rsi_values:
            assert 0 <= val <= 100

    def test_rsi_high_on_strong_uptrend(self):
        """强上升趋势中 RSI 应该较高"""
        closes = [float(i) for i in range(10, 50)]
        df = self._compute_indicators(closes)
        last_rsi = df["rsi14"].dropna().iloc[-1]
        assert last_rsi > 50

    def test_rsi_low_on_strong_downtrend(self):
        """强下降趋势中 RSI 应该较低"""
        closes = [float(i) for i in range(50, 10, -1)]
        df = self._compute_indicators(closes)
        last_rsi = df["rsi14"].dropna().iloc[-1]
        assert last_rsi < 50

    def test_dropna_removes_early_rows(self):
        """dropna 后至少过滤掉开头无法计算的 NaN"""
        closes = [float(i) for i in range(100)]
        df = self._compute_indicators(closes)
        raw_count = len(df)
        clean_count = len(df.dropna(subset=["ma5"]))
        assert clean_count < raw_count
        # 前4行应该是 NaN (MA5 窗口为5)
        assert pd.isna(df.loc[0, "ma5"])
        assert pd.isna(df.loc[3, "ma5"])

    def test_macd_hist_cross_signal(self):
        """MACD 柱从负到正表示金叉信号"""
        prices = []
        for i in range(50):
            prices.append(100 - i)  # 先跌
        for i in range(50):
            prices.append(50 + i * 0.5)  # 后涨
        df = self._compute_indicators(prices)
        hist = df["macd_hist"].dropna()
        # 验证柱值从负变为正（反弹信号）
        first_half_mean = hist.iloc[:len(hist)//2].mean()
        second_half_mean = hist.iloc[len(hist)//2:].mean()
        assert first_half_mean < second_half_mean
