import { ref, type Ref, type WatchOptions } from "vue";

// 动画配置
interface AnimationConfig {
  /** 动画持续时间（毫秒） */
  duration?: number;
  /** 缓动函数 */
  easing?: string;
  /** 延迟（毫秒） */
  delay?: number;
}

// 预定义缓动函数
const EASINGS = {
  linear: "linear",
  ease: "ease",
  easeIn: "ease-in",
  easeOut: "ease-out",
  easeInOut: "ease-in-out",
  // 贝塞尔曲线
  spring: "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
  smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
  bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
};

// 消息进入动画
export function useMessageEnterAnimation() {
  const isVisible = ref(false);
  const animationStyle = ref("");

  const enter = (config: AnimationConfig = {}) => {
    const { duration = 300, easing = EASINGS.smooth } = config;

    isVisible.value = true;
    animationStyle.value = `
      animation: messageEnter ${duration}ms ${easing} forwards;
    `;
  };

  const leave = () => {
    isVisible.value = false;
  };

  return {
    isVisible,
    animationStyle,
    enter,
    leave,
  };
}

// 打字机效果
export function useTypingEffect(
  options: {
    speed?: number;
    onComplete?: () => void;
  } = {},
) {
  const { speed = 30, onComplete } = options;

  const displayedText = ref("");
  const isTyping = ref(false);
  const currentIndex = ref(0);

  const type = (text: string) => {
    if (!text) {
      displayedText.value = "";
      return;
    }

    isTyping.value = true;
    currentIndex.value = 0;
    displayedText.value = "";

    let index = 0;
    const timer = setInterval(() => {
      if (index < text.length) {
        displayedText.value += text.charAt(index);
        index++;
      } else {
        clearInterval(timer);
        isTyping.value = false;
        onComplete?.();
      }
    }, speed);

    return timer;
  };

  const stop = () => {
    isTyping.value = false;
  };

  const reset = () => {
    displayedText.value = "";
    currentIndex.value = 0;
    isTyping.value = false;
  };

  return {
    displayedText,
    isTyping,
    currentIndex,
    type,
    stop,
    reset,
  };
}

// 渐显动画
export function useFadeIn(options: AnimationConfig = {}) {
  const { duration = 300, easing = "ease-out" } = options;

  const fadeStyle = computed(
    () => `
    opacity: 0;
    animation: fadeIn ${duration}ms ${easing} forwards;
  `,
  );

  return {
    fadeStyle,
  };
}

// 滑动动画
export function useSlideAnimation(
  direction: "up" | "down" | "left" | "right" = "up",
) {
  const translateMap = {
    up: "translateY(20px)",
    down: "translateY(-20px)",
    left: "translateX(20px)",
    right: "translateX(-20px)",
  };

  const slideStyle = computed(
    () => `
    opacity: 0;
    transform: ${translateMap[direction]};
    animation: slideIn 300ms cubic-bezier(0.4, 0, 0.2, 1) forwards;
  `,
  );

  return {
    slideStyle,
  };
}

// 脉冲动画（用于加载状态）
export function usePulseAnimation() {
  const pulseStyle =
    "animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite";

  return {
    pulseStyle,
  };
}

// 骨架屏动画
export function useSkeletonAnimation(active: boolean = true) {
  const skeletonStyle = computed(() => {
    if (!active) return "";
    return `
      background: linear-gradient(
        90deg,
        rgba(229, 231, 235, 0.4) 0%,
        rgba(229, 231, 235, 0.8) 50%,
        rgba(229, 231, 235, 0.4) 100%
      );
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite ease-in-out;
    `;
  });

  return {
    skeletonStyle,
  };
}

// 计数器动画
export function useCounterAnimation(
  targetValue: Ref<number>,
  options: {
    duration?: number;
    onComplete?: () => void;
  } = {},
) {
  const { duration = 1000, onComplete } = options;

  const displayValue = ref(targetValue.value);
  let animationFrame: number | null = null;

  const animate = () => {
    const startValue = displayValue.value;
    const endValue = targetValue.value;
    const startTime = performance.now();

    const step = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // 缓动函数
      const eased = 1 - Math.pow(1 - progress, 3);

      displayValue.value = Math.round(
        startValue + (endValue - startValue) * eased,
      );

      if (progress < 1) {
        animationFrame = requestAnimationFrame(step);
      } else {
        onComplete?.();
      }
    };

    animationFrame = requestAnimationFrame(step);
  };

  // 监听目标值变化
  watch(
    () => targetValue.value,
    () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
      animate();
    },
    { immediate: true },
  );

  const stop = () => {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }
  };

  return {
    displayValue,
    stop,
  };
}

// CSS 动画注入
export const ANIMATION_KEYFRAMES = `
  @keyframes messageEnter {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  @keyframes skeleton-loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }

  @keyframes typing {
    from {
      width: 0;
    }
    to {
      width: 100%;
    }
  }

  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0;
    }
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;
