import React from 'react';

export interface Props { name: string }

export const TExample: React.FC<Props> = ({ name }) => <span>{name}</span>;
