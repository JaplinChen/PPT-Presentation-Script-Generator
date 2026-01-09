import { Fragment } from 'react';
import './StepIndicator.css';

export default function StepIndicator({ currentStep, steps }) {
    const allSteps = steps;

    return (
        <div className="progress-steps">
            {allSteps.map((step, index) => (
                <Fragment key={step.number}>
                    <div
                        className={`step ${currentStep >= step.number ? 'active' : ''} ${currentStep > step.number ? 'completed' : ''}`}
                    >
                        <div className="step-number">{step.number}</div>
                        <div className="step-label">{step.label}</div>
                    </div>
                    {index < allSteps.length - 1 && <div className="step-divider"></div>}
                </Fragment>
            ))}
        </div>
    );
}
