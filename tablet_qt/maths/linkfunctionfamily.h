/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once

// #define LINK_FUNCTION_FAMILY_USE_AIC

#include <Eigen/Dense>
#include <functional>
#include <QString>


class LinkFunctionFamily
{
public:
    using LinkFnType = std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)>;
    using InvLinkFnType = std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)>;
    using DerivativeInvLinkFnType = std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)>;
    using VarianceFnType = std::function<Eigen::ArrayXXd(const Eigen::ArrayXXd&)>;
    using DevResidsFnType = std::function<Eigen::ArrayXd(
            const Eigen::ArrayXd&,  // y
            const Eigen::ArrayXd&,  // mu
            const Eigen::ArrayXd&  // wt
        )>;
    using ValidEtaFnType = std::function<bool(const Eigen::ArrayXd&)>;
    using ValidMuFnType = std::function<bool(const Eigen::ArrayXd&)>;
    using InitializeFnType = std::function<bool(  // returns: OK?
        QStringList&,  // errors
        const LinkFunctionFamily&,  // family
        Eigen::ArrayXd&,  // y
        Eigen::ArrayXd&,  // n
        Eigen::ArrayXd&,  // m
        Eigen::ArrayXd&,  // weights
        Eigen::ArrayXd&,  // start
        Eigen::ArrayXd&,  // etastart
        Eigen::ArrayXd&   // mustart
        )>;
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
    using AICFnType = std::function<double(
            const Eigen::ArrayXd&,  // y, definitely vector (from glm.fit)
            const Eigen::ArrayXd&,  // n (NO IDEA from R glm.fit)
            const Eigen::ArrayXd&,  // mu, definitely vector (from glm.fit)
            const Eigen::ArrayXd&,  // wt, definitely vector (from glm.fit)
            double  // dev, definitely scalar (from glm.fit)
        )>;
#endif

    LinkFunctionFamily(
            const QString& family_name,
            LinkFnType link_fn,
            InvLinkFnType inv_link_fn,
            DerivativeInvLinkFnType derivative_inv_link_fn,
            VarianceFnType variance_fn,
            DevResidsFnType dev_resids_fn,
            ValidEtaFnType valid_eta_fn,
            ValidMuFnType valid_mu_fn,
            InitializeFnType initialize_fn
#ifdef LINK_FUNCTION_FAMILY_USE_AIC
            , AICFnType aic_fn
#endif
            );
public:
    // For nasty hacks, like R does ;)
    QString family_name;  // "family" in R

    // Link function (e.g. logit):
    LinkFnType link_fn;

    // Inverse link function (e.g. logistic):
    InvLinkFnType inv_link_fn;

    // Derivative of the inverse link function ("mu.eta" in R):
    DerivativeInvLinkFnType derivative_inv_link_fn;

    // Variance function: gives the variance as a function of the mean; "the
    // part of the variance that depends on" the mean.
    // https://en.wikipedia.org/wiki/Variance_function
    // If the variance is independent of the mean, then this should return a
    // constant, probably 1.
    VarianceFnType variance_fn;

    // Something related to the deviance of the residuals... ("dev.resids" in R)
    DevResidsFnType dev_resids_fn;

    // Validate inputs
    ValidEtaFnType valid_eta_fn;
    ValidMuFnType valid_mu_fn;

    // GLM initialization (ugly eval() code in R)
    InitializeFnType initialize_fn;

#ifdef LINK_FUNCTION_FAMILY_USE_AIC
    // AIC (Aikake information criterion) calculation ("aic" in R)
    AICFnType aic_fn;
#endif
};


extern const QString LINK_FAMILY_NAME_GAUSSIAN;
extern const QString LINK_FAMILY_NAME_BINOMIAL;
extern const QString LINK_FAMILY_NAME_POISSON;

extern const LinkFunctionFamily LINK_FN_FAMILY_GAUSSIAN;  // default for glm() in R
extern const LinkFunctionFamily LINK_FN_FAMILY_LOGIT;