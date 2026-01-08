'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { showToast } from '@/utils/toast';
import { api } from '@/lib/api';
import Image from 'next/image';

interface SubscriptionModalProps {
  open: boolean;
  onClose: () => void;
  currentSubscription: number;
  onSuccess?: () => void;
}

const SUBSCRIPTION_PLANS = {
  1: {
    name: 'Premium',
    price: 100000,
    color: 'from-sky-500 to-blue-500',
    bgColor: 'from-sky-50 to-blue-50',
    features: [
      '45 câu hỏi/quiz',
      '2 lần dùng power-up',
      'Nhiều tính năng',
      'Hỗ trợ ưu tiên',
    ],
  },
  2: {
    name: 'Pro',
    price: 300000,
    color: 'from-purple-500 to-pink-500',
    bgColor: 'from-purple-50 to-pink-50',
    features: [
      '60 câu hỏi/quiz',
      '3 lần dùng power-up',
      'Tất cả tính năng',
      'Hỗ trợ VIP',
      'Badge đặc biệt',
    ],
  },
};

export default function SubscriptionModal({ open, onClose, currentSubscription, onSuccess }: SubscriptionModalProps) {
  const [selectedPlan, setSelectedPlan] = useState<1 | 2 | null>(null);
  const [loading, setLoading] = useState(false);
  const [paymentData, setPaymentData] = useState<{
    qr_url: string;
    transaction_ref: string;
    amount: number;
    bank_info: {
      bank_name: string;
      account_number: string;
      account_name: string;
      description: string;
    };
  } | null>(null);

  const handleSelectPlan = async (plan: 1 | 2) => {
    if (plan <= currentSubscription) {
      showToast.error('Bạn đã sử dụng gói này hoặc cao hơn');
      return;
    }

    setLoading(true);
    try {
      const response = await api.user.requestSubscriptionUpgrade({ target_subscription: plan });
      
      if (response.status === 200 && response.data) {
        const data = response.data as Record<string, unknown>;
        if (data.success) {
          setSelectedPlan(plan);
          setPaymentData({
            qr_url: data.qr_url as string,
            transaction_ref: data.transaction_ref as string,
            amount: data.amount as number,
            bank_info: data.bank_info as {
              bank_name: string;
              account_number: string;
              account_name: string;
              description: string;
            },
          });
        } else {
          showToast.error((data.message as string) || 'Không thể tạo yêu cầu nâng cấp');
        }
      } else {
        showToast.error('Có lỗi xảy ra. Vui lòng thử lại');
      }
    } catch (error) {
      console.error('Error requesting upgrade:', error);
      showToast.error('Có lỗi xảy ra. Vui lòng thử lại');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyInfo = (text: string) => {
    navigator.clipboard.writeText(text);
    showToast.success('Đã sao chép!');
  };

  const handleClose = () => {
    setSelectedPlan(null);
    setPaymentData(null);
    onClose();
  };

  const handlePaymentComplete = () => {
    showToast.success('Yêu cầu nâng cấp đã được ghi nhận. Admin sẽ xác nhận trong thời gian sớm nhất.');
    handleClose();
    onSuccess?.();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900">
            {paymentData ? 'Thanh toán nâng cấp' : 'Nâng cấp gói đăng ký'}
          </DialogTitle>
        </DialogHeader>

        {!paymentData ? (
          <div className="grid md:grid-cols-2 gap-6 py-4">
            {/* Premium Plan */}
            {currentSubscription < 1 && (
              <div className={`relative rounded-2xl border-2 border-sky-200 bg-gradient-to-br ${SUBSCRIPTION_PLANS[1].bgColor} p-6 hover:shadow-xl transition-all`}>
                <div className="absolute top-4 right-4">
                  <div className="px-3 py-1 rounded-full bg-gradient-to-r from-sky-500 to-blue-500 text-white text-sm font-bold">
                    {SUBSCRIPTION_PLANS[1].name}
                  </div>
                </div>
                
                <div className="mt-8 mb-6">
                  <div className="text-4xl font-black text-gray-900 mb-2">
                    {SUBSCRIPTION_PLANS[1].price.toLocaleString('vi-VN')}đ
                  </div>
                  <div className="text-sm text-gray-600">một lần / vĩnh viễn</div>
                </div>

                <div className="space-y-3 mb-6">
                  {SUBSCRIPTION_PLANS[1].features.map((feature, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-sky-600 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-sm text-gray-700 font-medium">{feature}</span>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={() => handleSelectPlan(1)}
                  disabled={loading}
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-sky-500 to-blue-500 hover:from-sky-600 hover:to-blue-600 text-white font-semibold shadow-lg"
                >
                  {loading ? 'Đang xử lý...' : 'Chọn Premium'}
                </Button>
              </div>
            )}

            {/* Pro Plan */}
            <div className={`relative rounded-2xl border-2 border-purple-200 bg-gradient-to-br ${SUBSCRIPTION_PLANS[2].bgColor} p-6 hover:shadow-xl transition-all ${currentSubscription >= 2 ? 'opacity-50' : ''}`}>
              <div className="absolute top-4 right-4 flex items-center gap-2">
                <div className="px-3 py-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-bold">
                  {SUBSCRIPTION_PLANS[2].name}
                </div>
                <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
              
              <div className="mt-8 mb-6">
                <div className="text-4xl font-black text-gray-900 mb-2">
                  {SUBSCRIPTION_PLANS[2].price.toLocaleString('vi-VN')}đ
                </div>
                <div className="text-sm text-gray-600">một lần / vĩnh viễn</div>
              </div>

              <div className="space-y-3 mb-6">
                {SUBSCRIPTION_PLANS[2].features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm text-gray-700 font-medium">{feature}</span>
                  </div>
                ))}
              </div>

              <Button
                onClick={() => handleSelectPlan(2)}
                disabled={loading || currentSubscription >= 2}
                className="w-full py-3 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Đang xử lý...' : currentSubscription >= 2 ? 'Đang sử dụng' : 'Chọn Pro'}
              </Button>
            </div>
          </div>
        ) : (
          <div className="py-4 space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Quét mã QR để thanh toán
              </h3>
              <p className="text-gray-600">
                Gói {SUBSCRIPTION_PLANS[selectedPlan!].name} - {paymentData.amount.toLocaleString('vi-VN')}đ
              </p>
            </div>

            <div className="flex justify-center">
              <div className="relative w-80 h-80 border-4 border-gray-200 rounded-2xl overflow-hidden shadow-lg">
                <Image
                  src={paymentData.qr_url}
                  alt="QR Code"
                  fill
                  className="object-contain p-4"
                  unoptimized
                />
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Ngân hàng:</span>
                <span className="text-sm font-bold text-gray-900">{paymentData.bank_info.bank_name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Số tài khoản:</span>
                <button
                  onClick={() => handleCopyInfo(paymentData.bank_info.account_number)}
                  className="text-sm font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  {paymentData.bank_info.account_number}
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Chủ tài khoản:</span>
                <span className="text-sm font-bold text-gray-900">{paymentData.bank_info.account_name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Số tiền:</span>
                <span className="text-sm font-bold text-green-600">{paymentData.amount.toLocaleString('vi-VN')}đ</span>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-medium text-gray-600">Nội dung:</span>
                  <button
                    onClick={() => handleCopyInfo(paymentData.bank_info.description)}
                    className="text-sm font-bold text-orange-600 hover:text-orange-700 flex items-center gap-1 text-right"
                  >
                    {paymentData.bank_info.description}
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
                <p className="text-xs text-amber-600 mt-2">⚠️ Vui lòng điền chính xác nội dung chuyển khoản</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">Hướng dẫn:</p>
                  <ol className="list-decimal list-inside space-y-1 text-xs">
                    <li>Mở app Vietcombank hoặc app ngân hàng có hỗ trợ VietQR</li>
                    <li>Quét mã QR hoặc chuyển khoản thủ công với thông tin trên</li>
                    <li>Đảm bảo nội dung chuyển khoản chính xác</li>
                    <li>Admin sẽ xác nhận và nâng cấp tài khoản trong 24h</li>
                  </ol>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={handleClose}
                variant="outline"
                className="flex-1"
              >
                Đóng
              </Button>
              <Button
                onClick={handlePaymentComplete}
                className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white"
              >
                Đã thanh toán
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
