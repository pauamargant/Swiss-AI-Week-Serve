import { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  return (
    <div className="main-container">
      {/* Background with gradient circles */}
      <div className="gradient-background">
        <svg
          width="1272"
          height="747"
          viewBox="0 0 1272 747"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="background-svg"
        >
          <g filter="url(#filter0_f_2011_7)">
            <circle cx="762" cy="590" r="140" fill="#89BCFF"></circle>
          </g>
          <g filter="url(#filter1_f_2011_7)">
            <circle cx="565" cy="707" r="207" fill="#FF86E1"></circle>
          </g>
          <defs>
            <filter
              id="filter0_f_2011_7"
              x="322"
              y="150"
              width="880"
              height="880"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
              <feBlend
                mode="normal"
                in="SourceGraphic"
                in2="BackgroundImageFix"
                result="shape"
              ></feBlend>
              <feGaussianBlur
                stdDeviation="150"
                result="effect1_foregroundBlur_2011_7"
              ></feGaussianBlur>
            </filter>
            <filter
              id="filter1_f_2011_7"
              x="-142"
              y="0"
              width="1414"
              height="1414"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
              <feBlend
                mode="normal"
                in="SourceGraphic"
                in2="BackgroundImageFix"
                result="shape"
              ></feBlend>
              <feGaussianBlur
                stdDeviation="250"
                result="effect1_foregroundBlur_2011_7"
              ></feGaussianBlur>
            </filter>
          </defs>
        </svg>
      </div>
      
      {/* Main content container */}
      <div className="content-container">
        {children}
      </div>
    </div>
  );
};