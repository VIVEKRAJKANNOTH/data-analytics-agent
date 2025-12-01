import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const ChartRenderer = ({ config }) => {
    const svgRef = useRef(null);
    const containerRef = useRef(null);

    useEffect(() => {
        if (!config || !svgRef.current || !containerRef.current) return;

        // Clear previous chart
        d3.select(svgRef.current).selectAll("*").remove();

        const { type, data, x_key, y_key, title, x_label, y_label } = config;

        // Dimensions
        const containerWidth = containerRef.current.clientWidth || 600;
        const margin = { top: 40, right: 30, bottom: 60, left: 60 };
        const width = containerWidth - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        const svg = d3.select(svgRef.current)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // Title
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", -10)
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("font-weight", "bold")
            .style("fill", "#f1f5f9")
            .text(title);

        // Scales and Axes
        let x, y;

        if (type === 'bar') {
            x = d3.scaleBand()
                .range([0, width])
                .domain(data.map(d => d[x_key]))
                .padding(0.2);

            y = d3.scaleLinear()
                .range([height, 0])
                .domain([0, d3.max(data, d => Number(d[y_key]))]);

            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .attr("transform", "translate(-10,0)rotate(-45)")
                .style("text-anchor", "end")
                .style("fill", "#94a3b8");

            svg.append("g")
                .call(d3.axisLeft(y))
                .selectAll("text")
                .style("fill", "#94a3b8");

            // Bars
            svg.selectAll("mybar")
                .data(data)
                .enter()
                .append("rect")
                .attr("x", d => x(d[x_key]))
                .attr("y", d => y(d[y_key]))
                .attr("width", x.bandwidth())
                .attr("height", d => height - y(d[y_key]))
                .attr("fill", "#3b82f6")
                .on("mouseover", function () { d3.select(this).attr("fill", "#60a5fa"); })
                .on("mouseout", function () { d3.select(this).attr("fill", "#3b82f6"); });

        } else if (type === 'line') {
            x = d3.scalePoint()
                .range([0, width])
                .domain(data.map(d => d[x_key]));

            y = d3.scaleLinear()
                .range([height, 0])
                .domain([0, d3.max(data, d => Number(d[y_key]))]);

            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .attr("transform", "translate(-10,0)rotate(-45)")
                .style("text-anchor", "end")
                .style("fill", "#94a3b8");

            svg.append("g")
                .call(d3.axisLeft(y))
                .selectAll("text")
                .style("fill", "#94a3b8");

            // Line
            svg.append("path")
                .datum(data)
                .attr("fill", "none")
                .attr("stroke", "#3b82f6")
                .attr("stroke-width", 2)
                .attr("d", d3.line()
                    .x(d => x(d[x_key]))
                    .y(d => y(d[y_key]))
                );

            // Dots
            svg.selectAll("mycircles")
                .data(data)
                .enter()
                .append("circle")
                .attr("fill", "#3b82f6")
                .attr("stroke", "none")
                .attr("cx", d => x(d[x_key]))
                .attr("cy", d => y(d[y_key]))
                .attr("r", 4);

        } else if (type === 'scatter') {
            x = d3.scaleLinear()
                .domain([0, d3.max(data, d => Number(d[x_key]))])
                .range([0, width]);

            y = d3.scaleLinear()
                .domain([0, d3.max(data, d => Number(d[y_key]))])
                .range([height, 0]);

            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .style("fill", "#94a3b8");

            svg.append("g")
                .call(d3.axisLeft(y))
                .selectAll("text")
                .style("fill", "#94a3b8");

            // Dots
            svg.append('g')
                .selectAll("dot")
                .data(data)
                .enter()
                .append("circle")
                .attr("cx", d => x(d[x_key]))
                .attr("cy", d => y(d[y_key]))
                .attr("r", 5)
                .style("fill", "#3b82f6")
                .style("opacity", 0.7);
        } else if (type === 'pie') {
            const radius = Math.min(width, height) / 2;
            const pieSvg = svg.append("g")
                .attr("transform", `translate(${width / 2},${height / 2})`);

            const color = d3.scaleOrdinal()
                .domain(data.map(d => d[x_key]))
                .range(d3.schemeSet2);

            const pie = d3.pie()
                .value(d => d[y_key]);

            const data_ready = pie(data);

            const arc = d3.arc()
                .innerRadius(0)
                .outerRadius(radius);

            pieSvg.selectAll('whatever')
                .data(data_ready)
                .enter()
                .append('path')
                .attr('d', arc)
                .attr('fill', d => color(d.data[x_key]))
                .attr("stroke", "#1e293b")
                .style("stroke-width", "2px")
                .style("opacity", 0.7);

            // Legend
            const legend = svg.append("g")
                .attr("transform", `translate(${width - 100}, 0)`);

            data.forEach((d, i) => {
                const legendRow = legend.append("g")
                    .attr("transform", `translate(0, ${i * 20})`);

                legendRow.append("rect")
                    .attr("width", 10)
                    .attr("height", 10)
                    .attr("fill", color(d[x_key]));

                legendRow.append("text")
                    .attr("x", 20)
                    .attr("y", 10)
                    .attr("text-anchor", "start")
                    .style("font-size", "12px")
                    .style("fill", "#94a3b8")
                    .text(d[x_key]);
            });
        }

        // Labels
        if (x_label && type !== 'pie') {
            svg.append("text")
                .attr("text-anchor", "middle")
                .attr("x", width / 2)
                .attr("y", height + margin.bottom - 10)
                .style("fill", "#94a3b8")
                .style("font-size", "12px")
                .text(x_label);
        }

        if (y_label && type !== 'pie') {
            svg.append("text")
                .attr("text-anchor", "middle")
                .attr("transform", "rotate(-90)")
                .attr("y", -margin.left + 20)
                .attr("x", -height / 2)
                .style("fill", "#94a3b8")
                .style("font-size", "12px")
                .text(y_label);
        }

    }, [config]);

    return (
        <div ref={containerRef} className="chart-renderer" style={{ width: '100%', overflowX: 'auto' }}>
            <svg ref={svgRef}></svg>
        </div>
    );
};

export default ChartRenderer;
